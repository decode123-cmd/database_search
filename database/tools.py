from functools import lru_cache
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs, MACCSkeys
from rdkit.Chem import rdMolAlign, rdShapeHelpers
from django.shortcuts import render
from django.shortcuts import render,redirect,HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
from psycopg2 import sql

# ----------------------------------------------------------------------------
# Search settings. These are quoted on the tool pages (templates/database/
# index.html), so keep the two in sync when changing them.
# ----------------------------------------------------------------------------
MORGAN_RADIUS = 2            # ECFP4-style circular fingerprint
MORGAN_NBITS = 2048

# 3D similarity: Crippen-O3A alignment, scored by shape Tanimoto.
QUERY_CONFORMERS = 10        # conformers generated for the query (RMS-pruned)
LARGE_QUERY_HEAVY_ATOMS = 40 # above this size only half as many conformers are used, to keep search time bounded
CONFORMER_PRUNE_RMS = 0.5    # Angstrom
CONFORMER_SEED = 42
MAX_QUERY_HEAVY_ATOMS = 70   # the pre-computed set tops out at 68; larger queries embed impractically slowly
MAX_REFERENCE_HEAVY_ATOMS = 50  # on-demand models for entries missing from the workbook (kept small: runs inside a web request)
EMBED_MAX_ITERATIONS = 50    # bounds the time spent on molecules that will not embed
THREED_WORKBOOK = Path(__file__).resolve().parent.parent / 'tools3d_with_mol_3d.xlsx'
THREED_SHEETS = ('cell_line', 'animal_studies', 'patient_studies')


def smiles_to_mol(smiles):
    if not isinstance(smiles, str) or not smiles.strip():
        return None  # blank cells are common in the curated tables
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES string")
        return mol
    except Exception as e:
        print(f"Error in SMILES parsing: {e}")
        return None


def calculate_2d_similarity(mol1, mol2):
    if mol1 is None or mol2 is None:
        return 0
    fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, MORGAN_RADIUS, nBits=MORGAN_NBITS)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, MORGAN_RADIUS, nBits=MORGAN_NBITS)
    return DataStructs.TanimotoSimilarity(fp1, fp2)


# Function to perform substructure search
def is_substructure(query_mol, candidate_mol):
    """True if the database molecule contains the query as a substructure."""
    if query_mol is None or candidate_mol is None:
        return False
    return candidate_mol.HasSubstructMatch(query_mol)


# Function to calculate MACCS key-based similarity
def calculate_maccs_similarity(mol1, mol2):
    if mol1 is None or mol2 is None:
        return 0
    fp1 = MACCSkeys.GenMACCSKeys(mol1)
    fp2 = MACCSkeys.GenMACCSKeys(mol2)
    return DataStructs.TanimotoSimilarity(fp1, fp2)


# ----------------------------------------------------------------------------
# 3D similarity
# ----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _workbook_models():
    """Pre-computed 3D structures (SMILES -> Mol) from tools3d_with_mol_3d.xlsx.

    Loaded once per process. Rows without a usable MOL_3D block are skipped.
    """
    models = {}
    for sheet in THREED_SHEETS:
        df = pd.read_excel(THREED_WORKBOOK, sheet_name=sheet,
                           usecols=['STR_LINK (SMILES)', 'MOL_3D'])
        df = df.dropna().drop_duplicates('STR_LINK (SMILES)')
        for smiles, block in zip(df['STR_LINK (SMILES)'], df['MOL_3D']):
            if smiles in models:
                continue
            mol = Chem.MolFromMolBlock(block, removeHs=False)
            if mol is not None and mol.GetNumConformers():
                models[smiles] = mol
    return models


_generated_models = {}  # SMILES -> Mol or None, for entries added after the workbook was built


def _embed_single_conformer(smiles):
    mol = smiles_to_mol(smiles)
    if mol is None or mol.GetNumHeavyAtoms() > MAX_REFERENCE_HEAVY_ATOMS:
        return None
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = CONFORMER_SEED
    params.maxIterations = EMBED_MAX_ITERATIONS
    if AllChem.EmbedMolecule(mol, params) != 0:
        return None
    AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    return mol


def get_reference_model(smiles):
    """3D model for a database SMILES: workbook first, generated on demand otherwise."""
    models = _workbook_models()
    if smiles in models:
        return models[smiles]
    if smiles not in _generated_models:
        _generated_models[smiles] = _embed_single_conformer(smiles)
    return _generated_models[smiles]


def embed_query_conformers(mol):
    """Return (hydrogen-added mol, [conformer ids]) for the query, UFF-optimised.

    Conformers come from ETKDGv3 (same recipe as the reference set) and are
    RMS-pruned, so rigid molecules get one conformer and flexible ones several.
    """
    if mol.GetNumHeavyAtoms() > MAX_QUERY_HEAVY_ATOMS:
        raise ValueError(f'Query is too large for 3D search (more than {MAX_QUERY_HEAVY_ATOMS} heavy atoms).')
    mol_h = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = CONFORMER_SEED
    params.maxIterations = EMBED_MAX_ITERATIONS
    params.pruneRmsThresh = CONFORMER_PRUNE_RMS
    n_conformers = QUERY_CONFORMERS if mol.GetNumHeavyAtoms() <= LARGE_QUERY_HEAVY_ATOMS else QUERY_CONFORMERS // 2
    conf_ids = list(AllChem.EmbedMultipleConfs(mol_h, n_conformers, params))
    if not conf_ids:
        raise ValueError('Could not generate a 3D structure for the query SMILES.')
    AllChem.UFFOptimizeMoleculeConfs(mol_h, maxIters=500)
    return mol_h, conf_ids


def shape_similarity_3d(probes, reference):
    """Best shape Tanimoto (0-1) over the query conformers.

    Each probe conformer is aligned onto the reference with Crippen-O3A, then
    scored with the shape Tanimoto of the aligned pair. Probes are copied, so
    the query is never modified and results do not depend on search order.
    """
    best = 0.0
    for probe in probes:
        probe = Chem.Mol(probe)
        try:
            rdMolAlign.GetCrippenO3A(probe, reference).Align()
            score = 1.0 - rdShapeHelpers.ShapeTanimotoDist(probe, reference)
        except Exception:
            continue  # alignment can fail for unusual atom types; skip that pair
        best = max(best, score)
    return best


def similarity_3d_scores(query_mol, smiles_values):
    """Score every distinct SMILES against the query.

    Returns (scores, n_distinct, n_without_model): scores maps SMILES -> shape
    Tanimoto, and n_without_model counts distinct SMILES with no usable 3D
    model (they cannot be searched). The database repeats the same drug across
    many studies, so each distinct structure is aligned only once.
    """
    query_h, conf_ids = embed_query_conformers(query_mol)
    probes = [Chem.Mol(query_h, confId=cid) for cid in conf_ids]

    distinct = {s for s in smiles_values if isinstance(s, str) and s.strip()}
    scores, missing = {}, 0
    for smiles in distinct:
        reference = get_reference_model(smiles)
        if reference is None:
            missing += 1
            continue
        scores[smiles] = shape_similarity_3d(probes, reference)
    return scores, len(distinct), missing
