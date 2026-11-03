from unittest import mock

from django.test import SimpleTestCase

COLUMNS = ['ID', 'DRUG', 'Technique']


class RecordingCursor:
    """Stands in for the database: remembers every statement and returns an empty result."""

    def __init__(self, log):
        self.log = log
        self.description = [(c,) for c in COLUMNS]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, list(params) if params else []))

    def fetchall(self):
        return []


class ConditionalSearchTests(SimpleTestCase):
    def setUp(self):
        self.log = []
        fake = mock.Mock()
        fake.cursor.side_effect = lambda: RecordingCursor(self.log)
        patcher = mock.patch('database.views.connection', fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def search(self, **data):
        base = {'table[]': ['cell_line'], 'field[]': ['DRUG'], 'query[]': ['gem'], 'operator[]': ['and']}
        base.update(data)
        return self.client.post('/conditional_search/', base)

    def where_queries(self):
        return [entry for entry in self.log if ' WHERE ' in entry[0]]

    def test_single_condition(self):
        response = self.search()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.where_queries(), [('SELECT * FROM "Browse_by_cell_line" WHERE "DRUG" ILIKE %s', ['%gem%'])])

    def test_operators_join_each_row_to_the_next(self):
        for operator, sql in (('and', 'AND'), ('or', 'OR'), ('not', 'AND NOT')):
            self.log.clear()
            self.search(**{'table[]': ['cell_line'] * 2, 'field[]': ['DRUG', 'Technique'], 'query[]': ['gem', 'flow'],
                           'operator[]': [operator, 'and']})
            self.assertEqual(self.where_queries(),
                             [(f'SELECT * FROM "Browse_by_cell_line" WHERE "DRUG" ILIKE %s {sql} "Technique" ILIKE %s', ['%gem%', '%flow%'])])

    def test_each_study_type_uses_the_real_table_name(self):
        for study, table in (('cell_line', 'Browse_by_cell_line'), ('animal_studies', 'Browse_by_animal_studies'),
                             ('patient_studies', 'Browse_by_Patient_Studies')):
            self.log.clear()
            self.search(**{'table[]': [study]})
            self.assertIn(f'FROM "{table}" WHERE', self.where_queries()[0][0])

    def test_a_field_that_is_not_a_column_never_reaches_the_sql(self):
        response = self.search(**{'field[]': ['DRUG" OR 1=1 --']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.where_queries(), [])

    def test_an_unknown_operator_never_reaches_the_sql(self):
        response = self.search(**{'table[]': ['cell_line'] * 2, 'field[]': ['DRUG', 'Technique'], 'query[]': ['a', 'b'],
                                  'operator[]': ['and 1=1 OR', 'and']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.where_queries(), [])

    def test_values_are_parameters_not_sql_text(self):
        self.search(**{'query[]': ["x'; DROP TABLE y; --"]})
        sql, params = self.where_queries()[0]
        self.assertNotIn('DROP', sql)
        self.assertEqual(params, ["%x'; DROP TABLE y; --%"])

    def test_unknown_database_and_incomplete_forms_are_rejected(self):
        self.assertEqual(self.search(**{'table[]': ['all_fields']}).status_code, 400)
        self.assertEqual(self.search(**{'table[]': ['bogus']}).status_code, 400)
        self.assertEqual(self.search(**{'query[]': []}).status_code, 400)
        self.assertEqual(self.where_queries(), [])

    def test_rows_for_another_database_are_skipped_without_crashing(self):
        response = self.search(**{'table[]': ['cell_line', 'animal_studies', 'cell_line'], 'field[]': ['DRUG', 'DRUG', 'Technique'],
                                  'query[]': ['a', 'b', 'c'], 'operator[]': ['or', 'and', 'and']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.where_queries(),
                         [('SELECT * FROM "Browse_by_cell_line" WHERE "DRUG" ILIKE %s OR "Technique" ILIKE %s', ['%a%', '%c%'])])
