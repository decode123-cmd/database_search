import csv
import io
import json
import re
from unittest import mock

import pandas as pd
from django.core.cache import cache
from django.test import SimpleTestCase

# The tests never open a database connection: the API's connection is replaced by in-memory tables, so
# `manage.py test` cannot reach the real (remote) database.
GEMCITABINE = 'NC1=NC(=O)N(C=C1)[C@@H]1O[C@H](CO)[C@@H](O)C1(F)F'
IMMUNE = ['Immune_System_function_unaffected', 'Immune_System-Function_enhanced/numbers_increased',
          'Immune_System-Function_inhibited/numbers_decreased',
          'Negative_Immune_System_regulation_-Function_enhanced/numbers_in']
BASE_COLUMNS = ['ID', 'Drug', 'Drug_category', 'STR_LINK_(SMILES)', 'PMID', 'Technique'] + IMMUNE + ['COMMENT']


def _frame(rows, extra=None):
    columns = BASE_COLUMNS + (extra or [])
    return pd.DataFrame([[row.get(c) for c in columns] for row in rows], columns=columns)


TABLES = {
    'Browse_by_cell_line': _frame([
        {'ID': 'CANIMM/1', 'Drug': 'Gemcitabine', 'Drug_category': 'nucleoside analogue', 'STR_LINK_(SMILES)': GEMCITABINE,
         'Technique': 'Flow cytometry', IMMUNE[1]: 'NK cells', 'COMMENT': 'first'},
        {'ID': 'CANIMM/2', 'Drug': 'Gemcitabine + cisplatin', 'Drug_category': 'nucleoside analogue', 'STR_LINK_(SMILES)': GEMCITABINE,
         'Technique': 'Western'},
        {'ID': 'CANIMM/3', 'Drug': 'Ethanol', 'STR_LINK_(SMILES)': 'CCO', 'Technique': 'Flow cytometry', 'COMMENT': 'uses μM doses'},
        {'ID': 'CANIMM/4', 'Drug': 'Mystery', 'STR_LINK_(SMILES)': None},
    ]),
    'Browse_by_animal_studies': _frame([
        {'ID': 'CANIMM/10', 'Drug': 'Gemcitabine', 'STR_LINK_(SMILES)': GEMCITABINE},
        {'ID': 'CANIMM/11', 'Drug': 'Ethanol', 'STR_LINK_(SMILES)': 'CCO'},
    ], extra=['ANIMAL STRAIN USED']),
    'Browse_by_Patient_Studies': _frame([
        {'ID': 'CANIMM/20', 'Drug': 'Lenalidomide', 'STR_LINK_(SMILES)': 'NC1=CC=CC2=C1CN(C1CCC(=O)NC1=O)C2=O'},
    ], extra=['PATIENT_SAMPLE']),
}


class FakeCursor:
    def __init__(self, tables):
        self.tables = tables
        self.description = None
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        match = re.match(r'SELECT (\*|COUNT\(\*\)) FROM "(.+)"$', sql.strip())
        frame = self.tables[match.group(2)]
        if match.group(1) == '*':
            self.description = [(c,) for c in frame.columns]
            self.rows = [tuple(None if pd.isna(v) else v for v in row) for row in frame.itertuples(index=False)]
        else:
            self.description = [('count',)]
            self.rows = [(len(frame),)]

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]


class FakeConnection:
    def __init__(self, tables):
        self.tables = tables

    def cursor(self):
        return FakeCursor(self.tables)


class ApiTestCase(SimpleTestCase):
    tables = TABLES

    def setUp(self):
        cache.clear()
        fake = FakeConnection(self.tables)
        for target in ('database.api.connection', 'database.views.connection'):
            patcher = mock.patch(target, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def get_json(self, url, status=200):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status, response.content[:300])
        return json.loads(response.content)


class BrowseApiTests(ApiTestCase):
    def test_index_lists_endpoints_and_allows_any_origin(self):
        response = self.client.get('/api/v1/')
        body = json.loads(response.content)
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        self.assertEqual(response['X-API-Version'], '1')
        self.assertEqual(body['study_types'], ['cell_line', 'animal_studies', 'patient_studies'])
        self.assertIn('download', body['endpoints'])

    def test_study_list_returns_every_column_and_paginates(self):
        body = self.get_json('/api/v1/studies/cell_line/')
        self.assertEqual((body['total'], body['count'], body['next']), (4, 4, None))
        self.assertEqual(list(body['results'][0]), BASE_COLUMNS)
        body = self.get_json('/api/v1/studies/cell_line/?limit=3&offset=0')
        self.assertEqual((body['count'], body['total']), (3, 4))
        self.assertIn('offset=3', body['next'])
        body = self.get_json('/api/v1/studies/cell_line/?limit=3&offset=3')
        self.assertEqual((body['count'], body['next']), (1, None))

    def test_missing_values_are_null_and_unicode_survives(self):
        body = self.get_json('/api/v1/studies/cell_line/?ID=CANIMM/3')
        record = body['results'][0]
        self.assertIsNone(record['Drug_category'])
        self.assertEqual(record['COMMENT'], 'uses μM doses')

    def test_field_filters_free_text_and_exact(self):
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?Drug=gemcitabine')['total'], 2)
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?drug=gemcitabine&exact=true')['total'], 1)
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?q=western')['total'], 1)
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?DRUG=gemcitabine&technique=western')['total'], 1)
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?DRUG=nothing-like-this')['total'], 0)

    def test_filters_are_literal_not_patterns(self):
        self.assertEqual(self.get_json('/api/v1/studies/cell_line/?q=.*')['total'], 0)

    def test_errors_are_json_and_say_what_is_valid(self):
        body = self.get_json('/api/v1/studies/cell_line/?NOPE=1', status=400)
        self.assertIn('Drug', body['valid_fields'])
        self.assertIn('valid_values', self.get_json('/api/v1/studies/bogus/', status=404))
        self.get_json('/api/v1/studies/cell_line/?limit=0', status=400)
        self.get_json('/api/v1/studies/cell_line/?limit=1001', status=400)
        self.get_json('/api/v1/studies/cell_line/?limit=abc', status=400)
        self.get_json('/api/v1/studies/cell_line/?format=xml', status=400)

    def test_csv_page(self):
        response = self.client.get('/api/v1/studies/cell_line/?format=csv&limit=2')
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8'))))
        self.assertEqual(rows[0], BASE_COLUMNS)
        self.assertEqual(len(rows), 3)

    def test_only_get_is_allowed(self):
        response = self.client.post('/api/v1/studies/cell_line/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'GET, HEAD')

    def test_fields_lists_each_table(self):
        body = self.get_json('/api/v1/fields/')
        self.assertIn('PATIENT_SAMPLE', body['patient_studies'])
        self.assertIn('ANIMAL STRAIN USED', body['animal_studies'])

    def test_status_counts_come_from_the_database(self):
        body = self.get_json('/api/v1/status/')
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['studies'], {'cell_line': 4, 'animal_studies': 2, 'patient_studies': 1})
        self.assertEqual(body['total'], 7)

    def test_status_reports_failure_with_503(self):
        broken = mock.Mock()
        broken.cursor.side_effect = RuntimeError('database down')
        with mock.patch('database.api.connection', broken), self.assertLogs('database.api', level='ERROR'):
            response = self.client.get('/api/v1/status/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content)['status'], 'error')


class DownloadApiTests(ApiTestCase):
    def test_csv_download_of_one_table(self):
        response = self.client.get('/api/v1/download/animal_studies.csv')
        self.assertIn('attachment; filename="cancerimmunodb_animal_studies.csv"', response['Content-Disposition'])
        rows = list(csv.DictReader(io.StringIO(response.content.decode('utf-8'))))
        self.assertEqual([r['ID'] for r in rows], ['CANIMM/10', 'CANIMM/11'])
        self.assertIn('ANIMAL STRAIN USED', rows[0])

    def test_json_download_is_a_plain_array(self):
        response = self.client.get('/api/v1/download/cell_line.json')
        records = json.loads(response.content)
        self.assertEqual(len(records), 4)
        self.assertEqual(records[2]['COMMENT'], 'uses μM doses')
        self.assertIsNone(records[3]['STR_LINK_(SMILES)'])

    def test_all_stacks_the_tables_and_adds_study_type(self):
        records = json.loads(self.client.get('/api/v1/download/all.json').content)
        self.assertEqual(len(records), 7)
        self.assertEqual({r['study_type'] for r in records}, {'cell_line', 'animal_studies', 'patient_studies'})
        rows = list(csv.DictReader(io.StringIO(self.client.get('/api/v1/download/all.csv').content.decode('utf-8'))))
        self.assertEqual(len(rows), 7)
        self.assertEqual(list(rows[0])[0], 'study_type')
        self.assertIn('PATIENT_SAMPLE', rows[0])

    def test_unknown_download_is_not_routed(self):
        self.assertEqual(self.client.get('/api/v1/download/cell_line.xml').status_code, 404)
        self.assertEqual(self.client.get('/api/v1/download/bogus.csv').status_code, 404)


class SimilarityApiTests(ApiTestCase):
    def test_2d_finds_the_query_itself_first(self):
        body = self.get_json('/api/v1/similarity/?smiles=' + GEMCITABINE)
        self.assertEqual(body['method'], '2d')
        self.assertEqual(body['score_field'], '2d_similarity')
        self.assertEqual([r['ID'] for r in body['results']], ['CANIMM/1', 'CANIMM/2'])
        self.assertEqual(body['results'][0]['2d_similarity'], 1.0)
        self.assertIn('COMMENT', body['results'][0])          # full records, not just the web table's columns
        self.assertNotIn('mol', body['results'][0])
        self.assertEqual(body['info']['entries_total'], 4)
        self.assertEqual(body['info']['entries_searched'], 3)  # the blank-SMILES row is skipped

    def test_other_methods_and_study_types(self):
        body = self.get_json('/api/v1/similarity/?method=substructure&smiles=CO&study_type=animal_studies')
        self.assertEqual([r['ID'] for r in body['results']], ['CANIMM/10', 'CANIMM/11'])
        body = self.get_json('/api/v1/similarity/?method=maccs&threshold=1&smiles=CCO&study_type=animal_studies')
        self.assertEqual([r['ID'] for r in body['results']], ['CANIMM/11'])

    def test_3d_search_works_through_the_api(self):
        body = self.get_json('/api/v1/similarity/?method=3d&smiles=CCO&study_type=animal_studies&threshold=0.9')
        self.assertEqual([r['ID'] for r in body['results']], ['CANIMM/11'])
        self.assertGreater(body['results'][0]['3d_similarity'], 0.9)

    def test_limit_applies_to_results_not_to_the_summary(self):
        body = self.get_json('/api/v1/similarity/?method=substructure&smiles=C&limit=1')
        self.assertEqual(body['count'], 1)
        self.assertEqual(len(body['results']), 1)
        self.assertGreater(body['info']['matches'], 1)

    def test_bad_requests_are_explained(self):
        self.get_json('/api/v1/similarity/', status=400)
        self.get_json('/api/v1/similarity/?smiles=not_a_smiles(', status=400)
        self.assertIn('valid_values', self.get_json('/api/v1/similarity/?smiles=CCO&method=magic', status=400))
        self.assertIn('between 0 and 1', self.get_json('/api/v1/similarity/?smiles=CCO&threshold=3', status=400)['error'])
        self.get_json('/api/v1/similarity/?smiles=CCO&study_type=bogus', status=400)
        self.assertIn('too large', self.get_json('/api/v1/similarity/?method=3d&smiles=' + 'C' * 150, status=400)['error'])
