from django.test import SimpleTestCase

from . import tools
from .views import _parse_threshold


class SubstructureTests(SimpleTestCase):
    def test_database_molecule_must_contain_the_query(self):
        benzene = tools.smiles_to_mol('c1ccccc1')
        toluene = tools.smiles_to_mol('Cc1ccccc1')
        self.assertTrue(tools.is_substructure(benzene, toluene))    # toluene contains a benzene ring
        self.assertFalse(tools.is_substructure(toluene, benzene))   # benzene does not contain toluene

    def test_missing_molecules_never_match(self):
        benzene = tools.smiles_to_mol('c1ccccc1')
        self.assertFalse(tools.is_substructure(benzene, None))
        self.assertFalse(tools.is_substructure(None, benzene))


class ThresholdTests(SimpleTestCase):
    def test_valid_blank_and_default(self):
        self.assertEqual(_parse_threshold('0.7', 0.5), (0.7, None))
        self.assertEqual(_parse_threshold('', 0.5), (0.5, None))
        self.assertEqual(_parse_threshold(None, 0.4), (0.4, None))

    def test_rejects_out_of_range_and_non_numbers(self):
        for raw in ('1.5', '-0.1', 'abc'):
            value, error = _parse_threshold(raw, 0.5)
            self.assertIsNone(value)
            self.assertTrue(error)


class SimilarityTests(SimpleTestCase):
    def test_identical_molecules_score_one(self):
        mol = tools.smiles_to_mol('ClCCN(CCCl)P1(=O)NCCCO1')
        self.assertEqual(tools.calculate_2d_similarity(mol, mol), 1.0)
        self.assertEqual(tools.calculate_maccs_similarity(mol, mol), 1.0)

    def test_blank_smiles_is_not_a_molecule(self):
        for blank in (None, '', '   ', float('nan')):
            self.assertIsNone(tools.smiles_to_mol(blank))


class ThreeDSimilarityTests(SimpleTestCase):
    def test_a_molecule_matches_its_own_3d_model(self):
        query = tools.smiles_to_mol('CCO')
        scores, distinct, missing = tools.similarity_3d_scores(query, ['CCO', 'CCO', None, ''])
        self.assertEqual((distinct, missing), (1, 0))   # duplicates and blanks are not scored twice
        self.assertGreater(scores['CCO'], 0.9)

    def test_unparsable_entries_are_counted_as_missing(self):
        query = tools.smiles_to_mol('CCO')
        scores, distinct, missing = tools.similarity_3d_scores(query, ['CCO', 'not a smiles'])
        self.assertEqual((distinct, missing), (2, 1))
        self.assertNotIn('not a smiles', scores)

    def test_oversized_query_is_rejected(self):
        query = tools.smiles_to_mol('C' * (tools.MAX_QUERY_HEAVY_ATOMS + 1))
        with self.assertRaises(ValueError):
            tools.similarity_3d_scores(query, ['CCO'])


class PerStructureScoringTests(SimpleTestCase):
    def test_scores_match_row_by_row_scoring_when_structures_repeat(self):
        import pandas as pd
        from .views import _per_structure
        smiles = ['CCO', 'CCO', 'c1ccccc1', None, 'CCO', 'c1ccccc1']
        df = pd.DataFrame({'STR_LINK_(SMILES)': smiles, 'mol': [tools.smiles_to_mol(s) for s in smiles]})
        query = tools.smiles_to_mol('CCN')
        by_structure = _per_structure(df, lambda mol: tools.calculate_2d_similarity(query, mol))
        row_by_row = df['mol'].apply(lambda mol: tools.calculate_2d_similarity(query, mol))
        self.assertEqual(list(by_structure), list(row_by_row))   # including the blank structure
