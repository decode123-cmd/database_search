import json
from unittest import mock

import pandas as pd
from django.test import SimpleTestCase

from . import all_search_count
from .importer import CONTROLLED_COLUMNS
from .test_api import FakeConnection

ENH, INH, UNA, NEG = (CONTROLLED_COLUMNS[k] for k in ('enhanced', 'inhibited', 'unaffected', 'negative'))
TECH = CONTROLLED_COLUMNS['technique']


def _index(**lists):
    longest = max(len(v) for v in lists.values())
    return pd.DataFrame({name: values + [None] * (longest - len(values)) for name, values in lists.items()})


INDEX = _index(Drug_category=['Nucleoside Analogue', 'Taxanes', 'MEK inhibitor', 'MEK inhibitors'],
               Cancer_Type=['Sarcoma', 'Rhabdomyosarcoma', 'Rectal', 'Colorectal Cancer'],
               Controlled_Technique=['Flow cytometry', 'ELISA'],
               Controlled_Immune_Term=['T cells', 'NK cells', 'PD-L1 / CD274'])

CELL = pd.DataFrame({
    'ID': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'Drug_category': ['Nucleoside Analogue', 'nucleoside  analogue ', 'Taxanes', 'Antibiotic', None],
    'Cancer_Type': ['Sarcoma', 'Rhabdomyosarcoma', 'Rectal', 'Colorectal Cancer', 'Sarcoma'],
    TECH: ['Flow cytometry; ELISA', 'flow cytometry', None, 'Western blot', 'ELISA'],
    ENH: ['NK cells; T cells', None, None, 'Macrophages', None],
    INH: ['T cells', None, None, None, None],
    UNA: [None, None, None, None, 'NK cells'],
    NEG: [None, 'PD-L1 / CD274; PD-L1 / CD274', None, None, None],
})
ANIMAL = pd.DataFrame({'ID': ['A1', 'A2'], 'Drug_category': ['Taxanes', 'MEK inhibitors'], 'Cancer_Type': ['Sarcoma', 'Sarcoma'],
                       TECH: ['ELISA', None], ENH: ['T cells', None], INH: [None, None], UNA: [None, None], NEG: [None, None]})
PATIENT = pd.DataFrame({'ID': ['P1'], 'Drug_category': ['MEK inhibitor'], 'Cancer_Type': ['Rectal'],
                        TECH: ['Flow cytometry'], ENH: [None], INH: [None], UNA: [None], NEG: [None]})

TABLES = {'Browse_by_cell_line': CELL, 'Browse_by_animal_studies': ANIMAL, 'Browse_by_Patient_Studies': PATIENT, 'Browse_by_index': INDEX}


class BrowseTestCase(SimpleTestCase):
    tables = TABLES

    def setUp(self):
        patcher = mock.patch.object(all_search_count, 'connection', FakeConnection(self.tables))
        patcher.start()
        self.addCleanup(patcher.stop)


class SingleValuedBrowseTests(BrowseTestCase):
    def test_drug_categories_match_exactly_ignoring_case_and_spacing(self):
        table = all_search_count.browse('drug_category')['table']
        self.assertEqual(table['Nucleoside Analogue'], {'Cell_Count': 2, 'Animal_Count': 0, 'Patient_Count': 0})
        self.assertEqual(table['MEK inhibitor']['Patient_Count'], 1)
        self.assertEqual(table['MEK inhibitors']['Animal_Count'], 1)      # "MEK inhibitor" does not swallow "MEK inhibitors"
        self.assertEqual(table['MEK inhibitor']['Animal_Count'], 0)

    def test_a_cancer_type_that_contains_another_is_not_double_counted(self):
        table = all_search_count.browse('cancer_type')['table']
        self.assertEqual(table['Sarcoma']['Cell_Count'], 2)               # not 3: "Rhabdomyosarcoma" is its own row
        self.assertEqual(table['Rhabdomyosarcoma']['Cell_Count'], 1)
        self.assertEqual(table['Rectal']['Cell_Count'], 1)
        self.assertEqual(table['Colorectal Cancer']['Cell_Count'], 1)

    def test_studies_outside_the_list_are_counted_separately_so_columns_add_up(self):
        result = all_search_count.browse('drug_category')
        self.assertEqual(result['totals'], {'Cell_Count': 5, 'Animal_Count': 2, 'Patient_Count': 1})
        self.assertEqual(result['unassigned'], {'Cell_Count': 2, 'Animal_Count': 0, 'Patient_Count': 0})   # "Antibiotic" and a blank
        for key in all_search_count.COUNT_TABLES:
            listed = sum(row[key] for row in result['table'].values())
            self.assertEqual(listed + result['unassigned'][key], result['totals'][key])


class TermBrowseTests(BrowseTestCase):
    def test_a_study_listing_several_cancer_types_is_counted_under_each(self):
        several = CELL.assign(Cancer_Type=['Sarcoma; Rectal', 'Rectal', 'Rectal', 'Rectal', 'Rectal'])
        with mock.patch.object(all_search_count, 'connection', FakeConnection({**TABLES, 'Browse_by_cell_line': several})):
            result = all_search_count.browse('cancer_type')
            behind = all_search_count.studies_with('cancer_type', 'cell_count', 'Sarcoma')
        self.assertEqual((result['table']['Sarcoma']['Cell_Count'], result['table']['Rectal']['Cell_Count']), (1, 5))
        self.assertEqual(list(behind['ID']), ['C1'])


    def test_technique_terms_are_counted_per_study_under_every_term(self):
        result = all_search_count.browse('technique')
        self.assertEqual(result['table']['Flow cytometry']['Cell_Count'], 2)    # one study lists two terms, another uses other casing
        self.assertEqual(result['table']['ELISA']['Cell_Count'], 2)
        self.assertEqual(result['unassigned']['Cell_Count'], 2)                 # a blank, and "Western blot" which is not in the list
        self.assertEqual((result['mentions'], result['listed']), (7, 6))

    def test_immune_terms_count_a_study_once_even_if_two_columns_list_the_term(self):
        table = all_search_count.browse('immune')['table']
        self.assertEqual(table['T cells']['Cell_Count'], 1)                     # enhanced and inhibited of the same study
        self.assertEqual(table['PD-L1 / CD274']['Cell_Count'], 1)               # repeated inside one cell
        self.assertEqual(table['NK cells'], {'Cell_Count': 2, 'Animal_Count': 0, 'Patient_Count': 0})

    def test_immune_outcomes_can_be_counted_one_at_a_time(self):
        self.assertEqual(all_search_count.browse('immune', 'enhanced')['table']['T cells'], {'Cell_Count': 1, 'Animal_Count': 1, 'Patient_Count': 0})
        self.assertEqual(all_search_count.browse('immune', 'inhibited')['table']['T cells']['Animal_Count'], 0)
        self.assertEqual(all_search_count.browse('immune', 'unaffected')['table']['NK cells']['Cell_Count'], 1)
        self.assertEqual(all_search_count.browse('immune', 'negative')['table']['PD-L1 / CD274']['Cell_Count'], 1)
        with self.assertRaises(ValueError):
            all_search_count.browse('immune', 'sideways')

    def test_the_studies_behind_a_count_are_exactly_that_many(self):
        for kind, outcome in (('technique', 'any'), ('immune', 'any'), ('immune', 'enhanced'), ('drug_category', 'any'), ('cancer_type', 'any')):
            result = all_search_count.browse(kind, outcome)
            for name, counts in result['table'].items():
                for key, field in (('Cell_Count', 'cell_count'), ('Animal_Count', 'animal_count'), ('Patient_Count', 'patient_count')):
                    behind = all_search_count.studies_with(kind, field, name.upper(), outcome)   # matching ignores case
                    self.assertEqual(len(behind), counts[key], (kind, outcome, name, key))

    def test_data_without_the_controlled_terms_says_what_is_missing(self):
        old = {name: frame.drop(columns=[c for c in frame.columns if c.startswith('Controlled')]) for name, frame in TABLES.items()}
        with mock.patch.object(all_search_count, 'connection', FakeConnection(old)):
            result = all_search_count.browse('immune')
        self.assertEqual((result['table'], result['missing']), ({}, 'Controlled_Immune_Term'))

    def test_invalid_requests_are_rejected(self):
        with self.assertRaises(ValueError):
            all_search_count.studies_with('technique', 'bogus_count', 'x')
        with self.assertRaises(ValueError):
            all_search_count.browse('bogus')


class BrowseViewTests(BrowseTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch('database.views.connection', FakeConnection(self.tables))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_each_browse_page_returns_counts_totals_and_the_unassigned(self):
        for url in ('/drug_category/', '/technique/', '/cancer_type/', '/immune_terms/'):
            body = json.loads(self.client.get(url).content)
            self.assertEqual(set(body) & {'table', 'totals', 'unassigned'}, {'table', 'totals', 'unassigned'}, url)
            self.assertEqual(body['totals'], {'Cell_Count': 5, 'Animal_Count': 2, 'Patient_Count': 1})

    def test_immune_page_takes_an_outcome_and_rejects_nonsense(self):
        body = json.loads(self.client.get('/immune_terms/?outcome=inhibited').content)
        self.assertEqual(body['table']['T cells']['Cell_Count'], 1)
        self.assertEqual(self.client.get('/immune_terms/?outcome=sideways').status_code, 400)

    def test_a_count_links_to_the_studies_behind_it(self):
        response = self.client.get('/browse_term/?kind=technique&field=cell_count&term=flow%20cytometry')
        self.assertEqual(response.status_code, 200)
        page = response.content.decode('utf-8')
        self.assertIn('C1', page)
        self.assertIn('C2', page)
        self.assertNotIn('C3', page)

    def test_bad_links_give_a_page_not_a_crash(self):
        response = self.client.get('/browse_term/?kind=bogus&field=cell_count&term=x')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid browse kind', response.content.decode('utf-8'))
