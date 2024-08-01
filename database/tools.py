import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs, MACCSkeys
from rdkit.Chem import rdMolAlign
from django.shortcuts import render
from django.shortcuts import render,redirect,HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
import pandas as pd
import psycopg2
from psycopg2 import sql


def smiles_to_mol(smiles):
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
    fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, 2)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, 2)
    return DataStructs.TanimotoSimilarity(fp1, fp2)


# Function to perform substructure search
def is_substructure(mol1, mol2):
    if mol1 is None or mol2 is None:
        return False
    return mol1.HasSubstructMatch(mol2)

def calculate_3d_similarity(mol1, mol2):
    if mol1 is None or mol2 is None:
        return -1  # Return -1 similarity if either molecule is invalid
    
    mol1 = Chem.AddHs(mol1)
    mol2 = Chem.AddHs(mol2)
    
    # Generate 3D coordinates
    try:
        AllChem.EmbedMolecule(mol1, AllChem.ETKDG())
        AllChem.UFFOptimizeMolecule(mol1)
        AllChem.EmbedMolecule(mol2, AllChem.ETKDG())
        AllChem.UFFOptimizeMolecule(mol2)
        
        # Align molecules and calculate similarity
        o3a = rdMolAlign.GetO3A(mol1, mol2)
        return o3a.Score()
    except Exception as e:
        print(f"Error in 3D similarity calculation: {e}")
        return -1  # Return -1 to indicate an error in similarity calculationn


# Function to calculate MACCS key-based similarity
def calculate_maccs_similarity(mol1, mol2):
    fp1 = MACCSkeys.GenMACCSKeys(mol1)
    fp2 = MACCSkeys.GenMACCSKeys(mol2)
    return DataStructs.TanimotoSimilarity(fp1, fp2)