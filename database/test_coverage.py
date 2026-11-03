import csv
import io
import tempfile
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from .coverage import check_candidates
from .test_api import TABLES, FakeConnection


class CoverageTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        patcher = mock.patch('database.api.connection', FakeConnection(TABLES))
        patcher.start()
        self.addCleanup(patcher.stop)

    def frames(self):
        from .api import STUDY_TYPES, _study_frame
        return {study: _study_frame(study) for study in STUDY_TYPES}

    def test_drug_in_every_study_type_missing_from_some_and_absent(self):
        rows = {r['query']: r for r in check_candidates(self.frames(), drugs=['gemcitabine', 'Lenalidomide', 'Pembrolizumab'])}
        self.assertEqual(rows['gemcitabine']['cell_line'], 2)           # includes the combination entry
        self.assertEqual(rows['gemcitabine']['status'], 'no entries in: patient_studies')
        self.assertEqual(rows['Lenalidomide']['status'], 'no entries in: cell_line, animal_studies')
        self.assertEqual(rows['Pembrolizumab']['status'], 'not in the database')

    def test_pmid_match_ignores_the_trailing_dot_zero(self):
        tables = {name: frame.copy() for name, frame in TABLES.items()}
        tables['Browse_by_cell_line']['PMID'] = ['21052994.0', None, None, None]
        tables['Browse_by_animal_studies']['PMID'] = ['21052994.0', None]
        tables['Browse_by_Patient_Studies']['PMID'] = ['21052994', ]
        with mock.patch('database.api.connection', FakeConnection(tables)):
            cache.clear()
            rows = check_candidates(self.frames(), pmids=['21052994', '21052994.0', '999'])
        self.assertEqual([r['status'] for r in rows], ['in all study types', 'in all study types', 'not in the database'])

    def test_command_prints_a_table_and_csv(self):
        out = io.StringIO()
        call_command('check_coverage', '--drug', 'gemcitabine', '--drug', 'Pembrolizumab', stdout=out)
        text = out.getvalue()
        self.assertIn('no entries in: patient_studies', text)
        self.assertIn('not in the database', text)
        out = io.StringIO()
        call_command('check_coverage', '--drug', 'gemcitabine', '--csv', stdout=out)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual((rows[0]['query'], rows[0]['cell_line']), ('gemcitabine', '2'))

    def test_command_reads_a_csv_file(self):
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, newline='') as handle:
            handle.write('Drug,PMID\nLenalidomide,\n,27687804\n')
        out = io.StringIO()
        call_command('check_coverage', '--file', handle.name, '--csv', stdout=out)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual([(r['kind'], r['query']) for r in rows], [('drug', 'Lenalidomide'), ('pmid', '27687804')])

    def test_command_needs_something_to_look_for(self):
        with self.assertRaises(CommandError):
            call_command('check_coverage')

    def test_older_tables_with_an_upper_case_drug_column_still_work(self):
        tables = {name: frame.rename(columns={'Drug': 'DRUG'}) for name, frame in TABLES.items()}
        with mock.patch('database.api.connection', FakeConnection(tables)):
            cache.clear()
            rows = check_candidates(self.frames(), drugs=['gemcitabine'])
        self.assertEqual(rows[0]['cell_line'], 2)
