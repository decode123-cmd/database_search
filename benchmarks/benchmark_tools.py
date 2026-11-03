"""Benchmark of the CancerImmunoDB structure searches (reviewer comment R1-5).

Two parts, because the comparison needs Open Babel and the timings need the project's own environment:

  python benchmarks/benchmark_tools.py --part openbabel --csv all.csv
      Agreement with Open Babel on 2D similarity, MACCS similarity and substructure search.
      Needs RDKit and Open Babel (python bindings) in the same environment.

  python benchmarks/benchmark_tools.py --part app --csv all.csv
      Run time of the four searches, stability of the 3D search, and a check that the app's functions give the same
      numbers as the plain RDKit calls used in the first part. Needs the project's environment (Django, RDKit).

all.csv is the full download from the site: https://<site>/api/v1/download/all.csv
"""
import argparse
import os
import platform
import random
import sys
import time
import warnings

import pandas as pd
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import AllChem, MACCSkeys

RDLogger.DisableLog('rdApp.*')
warnings.filterwarnings('ignore')
SMILES = 'STR_LINK_(SMILES)'
QUERY_DRUGS = ['Daunorubicin', 'Doxorubicin', 'Gemcitabine', 'Lenalidomide', 'Decitabine', 'Imatinib', 'Cyclophosphamide',
               'Sorafenib', 'Paclitaxel', 'Vorinostat']
FRAGMENTS = {'glutarimide ring': 'O=C1CCCC(=O)N1', 'benzene ring': 'c1ccccc1', 'pyrimidine ring': 'c1cncnc1', 'indole': 'c1ccc2[nH]ccc2c1',
             'pyridine ring': 'c1ccncc1', 'carboxylic acid': 'C(=O)O', 'amide': 'C(=O)N', 'sulfonamide': 'S(=O)(=O)N'}


def load(csv_path):
    df = pd.read_csv(csv_path, dtype=str)
    df = df[df[SMILES].fillna('').str.strip() != '']
    df['mol'] = df[SMILES].map(lambda s: Chem.MolFromSmiles(s))
    rows = df[df['mol'].notna()].reset_index(drop=True)       # what the app searches: one entry per study row
    distinct = rows.drop_duplicates(SMILES).reset_index(drop=True)
    queries = {}
    for name in QUERY_DRUGS:
        hit = distinct[distinct['DRUG'].fillna('').str.contains(name, case=False, regex=False) & ~distinct[SMILES].str.contains(',|\n', regex=True)]
        if len(hit):
            queries[name] = hit.iloc[0][SMILES]
    return df, rows, distinct, queries


def rd_morgan(m):
    return AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)


def spearman(a, b):
    return pd.Series(a).rank().corr(pd.Series(b).rank())  # Pearson on average ranks = Spearman (no scipy needed)


def top_overlap(a, b, k=10):
    top = lambda s: set(pd.Series(s).sort_values(ascending=False, kind='stable').head(k).index[[v > 0 for v in pd.Series(s).sort_values(ascending=False, kind='stable').head(k)]])
    ta, tb = top(a), top(b)
    return len(ta & tb) / max(len(ta | tb), 1)


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def header(title):
    print(f'\n### {title}\n')


def part_openbabel(csv_path):
    from openbabel import openbabel as ob, pybel
    ob.obErrorLog.SetOutputLevel(0)
    df, rows, distinct, queries = load(csv_path)
    print(f'RDKit {rdBase.rdkitVersion}, Open Babel {ob.OBReleaseVersion()}')
    print(f'{len(df)} study rows in the file, {len(rows)} with a structure RDKit reads, {len(distinct)} distinct structures; {len(queries)} query drugs.')

    def ob_mol(smiles):
        try:
            return pybel.readstring('smi', smiles)
        except Exception:
            return None

    obm = [ob_mol(s) for s in distinct[SMILES]]
    keep = [i for i, m in enumerate(obm) if m is not None]
    distinct = distinct.iloc[keep].reset_index(drop=True)
    obm = [obm[i] for i in keep]
    print(f'{len(distinct)} distinct structures read by both toolkits (used below).')
    rd_morgan_fps = [rd_morgan(m) for m in distinct['mol']]
    rd_maccs_fps = [MACCSkeys.GenMACCSKeys(m) for m in distinct['mol']]
    ob_ecfp = [m.calcfp('ecfp4') for m in obm]
    ob_maccs = [m.calcfp('maccs') for m in obm]

    header('2D similarity: RDKit Morgan (radius 2, 2048 bits) against Open Babel ECFP4, Tanimoto')
    out = []
    for name, smi in queries.items():
        qr, qo = Chem.MolFromSmiles(smi), ob_mol(smi)
        a = DataStructs.BulkTanimotoSimilarity(rd_morgan(qr), rd_morgan_fps)
        b = [qo.calcfp('ecfp4') | f for f in ob_ecfp]
        hits_a = [i for i, v in enumerate(a) if v >= 0.5]
        hits_b = [i for i, v in enumerate(b) if v >= 0.5]
        out.append((name, spearman(a, b), top_overlap(a, b), len(hits_a), len(hits_b), jaccard(hits_a, hits_b)))
    print('| Query | Spearman rho | Top-10 overlap | Hits at 0.5 (RDKit) | Hits at 0.5 (Open Babel) | Hit-set overlap |\n| --- | --- | --- | --- | --- | --- |')
    for r in out:
        print(f'| {r[0]} | {r[1]:.3f} | {r[2]:.2f} | {r[3]} | {r[4]} | {r[5]:.2f} |')
    print(f'\nMean rho {sum(r[1] for r in out) / len(out):.3f} (lowest {min(r[1] for r in out):.3f}); mean top-10 overlap {sum(r[2] for r in out) / len(out):.2f}.')

    header('MACCS similarity: RDKit MACCS keys against Open Babel MACCS, Tanimoto')
    out = []
    for name, smi in queries.items():
        qr, qo = Chem.MolFromSmiles(smi), ob_mol(smi)
        a = DataStructs.BulkTanimotoSimilarity(MACCSkeys.GenMACCSKeys(qr), rd_maccs_fps)
        b = [qo.calcfp('maccs') | f for f in ob_maccs]
        diffs = [abs(x - y) for x, y in zip(a, b)]
        out.append((name, spearman(a, b), pd.Series(a).corr(pd.Series(b)), sum(diffs) / len(diffs), top_overlap(a, b)))
    print('| Query | Spearman rho | Pearson r | Mean absolute difference | Top-10 overlap |\n| --- | --- | --- | --- | --- |')
    for r in out:
        print(f'| {r[0]} | {r[1]:.3f} | {r[2]:.3f} | {r[3]:.3f} | {r[4]:.2f} |')
    print(f'\nMean rho {sum(r[1] for r in out) / len(out):.3f}; mean absolute difference {sum(r[3] for r in out) / len(out):.3f}.')

    header('Substructure search: RDKit against Open Babel SMARTS matching (distinct structures that contain the fragment)')
    print('A fragment typed as SMILES matches on element and bond type only, like the element-only SMARTS that RDKit writes for it.\n'
          'Open Babel reads a typed SMARTS strictly (for example [nH] needs exactly one hydrogen, N needs a non-aromatic nitrogen),\n'
          'so each fragment is also given to Open Babel in that element-only form.\n')
    print('| Fragment | RDKit | Open Babel, SMARTS as typed | Same structures | Open Babel, element-only SMARTS | Same structures |\n| --- | --- | --- | --- | --- | --- |')
    for name, frag in FRAGMENTS.items():
        q = Chem.MolFromSmiles(frag)
        a = [i for i, m in enumerate(distinct['mol']) if m.HasSubstructMatch(q)]
        typed = pybel.Smarts(frag)
        b = [i for i, m in enumerate(obm) if typed.findall(m)]
        elemental = pybel.Smarts(Chem.MolToSmarts(q))
        c = [i for i, m in enumerate(obm) if elemental.findall(m)]
        print(f'| {name} | {len(a)} | {len(b)} | {jaccard(a, b):.2f} | {len(c)} | {jaccard(a, c):.2f} |')


def part_app(csv_path):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import tools
    df, rows, distinct, queries = load(csv_path)
    print(f'RDKit {rdBase.rdkitVersion}, Python {platform.python_version()}, {platform.machine()}, {os.cpu_count()} logical CPUs, one process.')
    print(f'{len(rows)} study rows with a structure, {len(distinct)} distinct structures, {len(queries)} query drugs.')

    header('The app computes what plain RDKit computes')
    rng, pairs = random.Random(1), []
    mols = list(rows['mol'])
    for _ in range(500):
        pairs.append((rng.choice(mols), rng.choice(mols)))
    same_2d = all(abs(tools.calculate_2d_similarity(a, b) - DataStructs.TanimotoSimilarity(rd_morgan(a), rd_morgan(b))) < 1e-12 for a, b in pairs)
    same_maccs = all(abs(tools.calculate_maccs_similarity(a, b) - DataStructs.TanimotoSimilarity(MACCSkeys.GenMACCSKeys(a), MACCSkeys.GenMACCSKeys(b))) < 1e-12 for a, b in pairs)
    same_sub = all(tools.is_substructure(a, b) == b.HasSubstructMatch(a) for a, b in pairs)
    print(f'500 random pairs: 2D identical = {same_2d}, MACCS identical = {same_maccs}, substructure identical = {same_sub}.')

    header('Run time per search (the same search functions the website runs: one query against every study row)')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cancer_immuno.settings')
    import django
    django.setup()
    from database import views
    table = rows.copy()
    table['valid_smiles'] = True
    benzene = Chem.MolFromSmiles('c1ccccc1')
    timings = {'2D': [], 'MACCS': [], 'substructure': [], '3D': []}
    for name, smi in queries.items():
        q = Chem.MolFromSmiles(smi)
        for key, function, query, threshold in (('2D', views._search_2d, q, 0.5), ('MACCS', views._search_maccs, q, 0.5),
                                                ('substructure', views._search_substructure, benzene, None), ('3D', views._search_3d, q, 0.5)):
            t = time.perf_counter(); function(table.copy(), query, threshold); timings[key].append(time.perf_counter() - t)
    print('| Search | Median | Slowest |\n| --- | --- | --- |')
    for k, v in timings.items():
        v = sorted(v)
        print(f'| {k} | {v[len(v) // 2]:.3f} s | {v[-1]:.3f} s |')

    header('3D search: does the ranking depend on the random seed used to build the query conformers?')
    original_seed = tools.CONFORMER_SEED
    print('| Query | Spearman rho (seed 42 vs 7) | Spearman rho (seed 42 vs 123) | Top-10 overlap (42 vs 7) | Own score | Own rank |\n| --- | --- | --- | --- | --- |  --- |')
    rhos = []
    for name, smi in queries.items():
        runs = {}
        for seed in (42, 7, 123):
            tools.CONFORMER_SEED = seed
            runs[seed], _, _ = tools.similarity_3d_scores(Chem.MolFromSmiles(smi), list(distinct[SMILES]))
        tools.CONFORMER_SEED = original_seed
        keys = sorted(runs[42])
        s42, s7, s123 = ([runs[s].get(k, 0.0) for k in keys] for s in (42, 7, 123))
        own = runs[42].get(smi)
        rank = (sorted(runs[42].values(), reverse=True).index(own) + 1) if own is not None else None
        rhos.append((spearman(s42, s7), spearman(s42, s123)))
        print(f'| {name} | {rhos[-1][0]:.3f} | {rhos[-1][1]:.3f} | {top_overlap(s42, s7):.2f} | {own if own is None else round(own, 2)} | {rank} of {len(keys)} |')
    print(f'\nMean rho {sum(r[0] for r in rhos) / len(rhos):.3f} (seed 7) and {sum(r[1] for r in rhos) / len(rhos):.3f} (seed 123).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--part', choices=['openbabel', 'app'], required=True)
    parser.add_argument('--csv', required=True, help='all.csv downloaded from the site')
    args = parser.parse_args()
    {'openbabel': part_openbabel, 'app': part_app}[args.part](args.csv)
