import io
import os
import tempfile
from unittest import mock

import pandas as pd
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from sqlalchemy import create_engine, inspect

from . import importer

CELL = pd.DataFrame({
    'ID': ['CANIMM/1', 'CANIMM/2', 'CANIMM/3'],
    'Drug': ['Gemcitabine ', 'Taxol', 'Lenalidomide'],
    'Drug category': ['Nucleoside Analogue', 'Taxanes', 'Antibiotic'],
    'Pubchem ID': [60750.0, 41774.0, None],
    'STR_LINK (SMILES)': ['CCO', 'CCN', None],
    'PMID': [27687804, 26637667.0, None],
    'Cancer_Type': ['Sarcoma', 'Rectal', 'Rectal'],
    'Technique': ['Flow', 'ELISA', ''],
    'Controlled Technique 1': ['Flow cytometry; ELISA', 'Western blot', None],
    'Controlled_Terms_Function enhaved/Number_increased': ['NK cells; T cells', None, 'Macrophages'],
    'Controlled_Terms_Function inhibited/numbers decreased': ['T cells', None, None],
    'Controlled_Terms_Unaffected': [None, None, None],
    'Controlled_Terms_Negative_Regulation': [None, 'PD-L1 / CD274', None],
    'Unnamed: 14': [None, 'a note with no heading', None],
})
ANIMAL = pd.DataFrame({
    'ID': ['CANIMM/10'], 'Drug': ['Gemcitabine'], 'Drug category': ['Taxanes'], 'Drug_Pubchem': [60750], 'STR_LINK (SMILES)': ['CCO'],
    'PMID': [111], 'Cancer_Type': ['Sarcoma'], 'Technique': ['ELISA'], 'Controlled Technique 2': ['ELISA'],
    'Controlled_Terms_Function_enhanced_Number_increased': ['T cells'],
    'Controlled_Terms_Function_inhibited_Number_decreased': [None],
})
PATIENT = pd.DataFrame({
    'ID': ['CANIMM/20'], 'Drug': ['Pomalidomide'], 'Drug category': ['Nucleoside Analogue'], 'Pubchem ID': ['9'], 'STR_LINK (SMILES)': [None],
    'PMID': ['222'], 'Cancer_Type': ['Sarcoma'], 'Male/Female': ['2024-06-04 00:00:00'], 'Technique': ['ELISA'],
    'Controlled Technique 3': ['ELISA'], 'Controlled_Terms_Function enhaved/Number_increased': ['NK cells'],
    'Controlled_Terms_Function_inhibited/Number_decreased': ['Treg'],
})
INDEX = pd.DataFrame({
    'Drug category1': ['Nucleoside Analogue', 'Taxanes', 'taxanes ', 'Antibiotics'], 'Cell Line': ['absent', None, None, None],
    'Cancer_Type': ['Sarcoma', 'Rectal', None, None],
    'Controlled word': ['Flow cytometry', 'ELISA', 'Western blot', None],
    'Controlled word.1': ['T cells', 'NK cells', 'PD-L1 / CD274', 'PD-L1/CD274'],
})


def write_workbook(path, **overrides):
    sheets = {'cell line': CELL, 'Animal study': ANIMAL, 'Patient study': PATIENT, 'Browse by index': INDEX}
    sheets.update(overrides)
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, frame in sheets.items():
            if frame is not None:
                frame.to_excel(writer, sheet_name=name, index=False)


class WorkbookTestCase(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, 'data.xlsx')
        write_workbook(self.path)


class ReadWorkbookTests(WorkbookTestCase):
    def test_sheets_become_the_tables_the_site_reads(self):
        tables, notes = importer.read_workbook(self.path)
        self.assertEqual(set(tables), {'Browse_by_cell_line', 'Browse_by_animal_studies', 'Browse_by_Patient_Studies', 'Browse_by_index', 'Master'})
        self.assertEqual([len(tables[t]) for t in ('Browse_by_cell_line', 'Browse_by_animal_studies', 'Browse_by_Patient_Studies', 'Master')], [3, 1, 1, 5])

    def test_the_old_sheet_names_are_accepted_too(self):
        write_workbook(self.path, **{'Browse by cell line': CELL, 'Browse by animal studies': ANIMAL, 'Browse by Patient Studies': PATIENT},
                       **{'cell line': None, 'Animal study': None, 'Patient study': None})
        tables, notes = importer.read_workbook(self.path)
        self.assertEqual(notes['missing_sheets'], [])
        self.assertEqual(len(tables['Browse_by_cell_line']), 3)

    def test_old_columns_keep_their_names_and_the_controlled_columns_get_one_spelling(self):
        tables, _ = importer.read_workbook(self.path)
        cell, animal, patient = (tables[t] for t in ('Browse_by_cell_line', 'Browse_by_animal_studies', 'Browse_by_Patient_Studies'))
        self.assertEqual(list(cell.columns)[:4], ['ID', 'Drug', 'Drug_category', 'Pubchem_ID'])      # as the old importer named them
        self.assertIn('STR_LINK_(SMILES)', cell.columns)
        for frame in (cell, animal, patient):
            self.assertIn('Controlled_Terms_Function_enhanced_Number_increased', frame.columns)
            self.assertIn('Controlled_Terms_Function_inhibited_Number_decreased', frame.columns)
            self.assertIn('Controlled_Technique', frame.columns)
        self.assertIn('Drug_Pubchem', animal.columns)                                               # left as the sheet has it

    def test_identifiers_lose_the_dot_zero_and_text_is_trimmed(self):
        cell = importer.read_workbook(self.path)[0]['Browse_by_cell_line']
        self.assertEqual(list(cell['PMID'][:2]), ['27687804', '26637667'])
        self.assertEqual(cell['Pubchem_ID'][0], '60750')
        self.assertEqual(cell['Drug'][0], 'Gemcitabine')
        self.assertIsNone(cell['Technique'][2])           # an empty cell becomes a missing value

    def test_a_note_in_a_column_without_a_heading_is_reported_not_silently_lost(self):
        tables, notes = importer.read_workbook(self.path)
        self.assertNotIn('Unnamed: 14', tables['Browse_by_cell_line'].columns)
        self.assertEqual(notes['dropped_notes'][0]['rows_with_text'], 1)
        self.assertIn('a note with no heading', notes['dropped_notes'][0]['example'])

    def test_the_index_lists_become_tidy_columns(self):
        index = importer.read_workbook(self.path)[0]['Browse_by_index']
        self.assertEqual(list(index.columns), ['Drug_category', 'Cancer_Type', 'Controlled_Technique', 'Controlled_Immune_Term'])
        self.assertEqual(list(index['Drug_category'].dropna()), ['Nucleoside Analogue', 'Taxanes', 'Antibiotics'])   # "taxanes " was a repeat
        self.assertEqual(len(index['Controlled_Technique'].dropna()), 3)

    def test_master_stacks_the_studies_and_says_which_is_which(self):
        master = importer.read_workbook(self.path)[0]['Master']
        self.assertEqual(master['Study_type'].value_counts().to_dict(), {'cell_line': 3, 'animal_studies': 1, 'patient_studies': 1})

    def test_two_columns_that_would_clash_stop_the_import(self):
        clash = CELL.rename(columns={'Pubchem ID': 'Pubchem_ID'}).assign(**{'Pubchem ID': 1})
        write_workbook(self.path, **{'cell line': clash})
        with self.assertRaises(ValueError):
            importer.read_workbook(self.path)


class CheckTests(WorkbookTestCase):
    def report(self):
        tables, _ = importer.read_workbook(self.path)
        return importer.check(tables)

    def test_coverage_of_the_controlled_lists(self):
        coverage = self.report()['coverage']
        self.assertEqual((coverage['technique']['mentions'], coverage['technique']['in_list']), (5, 5))
        self.assertEqual(coverage['immune']['mentions'], 8)
        self.assertEqual(coverage['immune']['in_list'], 6)                      # "Macrophages" and "Treg" are not listed; the rest are
        self.assertEqual(coverage['technique']['list_never_used'], [])

    def test_terms_missing_from_the_list_come_with_a_close_match(self):
        rows = {r['term in data']: r for r in self.report()['worklists']['Immune term not in the controlled list']}
        self.assertIn('Macrophages', rows)
        self.assertIn('Treg', rows)

    def test_list_entries_that_differ_only_in_punctuation_are_flagged(self):
        twins = self.report()['worklists']['List entries that are near-duplicates']
        self.assertTrue(any('PD-L1 / CD274' in t['entries'] and 'PD-L1/CD274' in t['entries'] for t in twins))

    def test_values_outside_the_index_lists_are_listed(self):
        rows = self.report()['worklists']['Drug category not in the index list']
        self.assertEqual({r['value in data'] for r in rows}, {'Antibiotic'})
        self.assertEqual(rows[0]['closest list entry'], 'Antibiotics')

    def test_sex_ratios_turned_into_dates_are_found(self):
        report = self.report()
        self.assertEqual(report['tables']['patient_studies']['sex_ratio_dates'], 1)
        self.assertEqual(report['worklists']['Sex ratio turned into a date'][0]['ID'], 'CANIMM/20')

    def test_duplicate_ids_are_found(self):
        write_workbook(self.path, **{'cell line': pd.concat([CELL, CELL.iloc[[0]]])})
        self.assertEqual(self.report()['tables']['cell_line']['duplicate_ids'], ['CANIMM/1'])


class ImportCommandTests(WorkbookTestCase):
    def setUp(self):
        super().setUp()
        self.db_path = os.path.join(self.dir.name, 'site.sqlite3')
        self.engine = create_engine(f'sqlite:///{self.db_path}')

    def run_command(self, *args, **kwargs):
        out = io.StringIO()
        with mock.patch('database.management.commands.import_excel.database_engine', return_value=self.engine):
            call_command('import_excel', '--file', self.path, *args, stdout=out, **kwargs)
        return out.getvalue()

    def tables(self):
        return set(inspect(self.engine).get_table_names())

    def test_a_dry_run_reports_and_writes_nothing(self):
        text = self.run_command()
        self.assertIn('Dry run', text)
        self.assertIn('controlled immune terms', text)
        self.assertEqual(self.tables(), set())

    def test_a_dry_run_never_asks_for_the_database(self):
        with mock.patch('database.management.commands.import_excel.database_engine', side_effect=AssertionError('touched the database')):
            call_command('import_excel', '--file', self.path, stdout=io.StringIO())

    def test_apply_needs_confirmation_and_cancelling_writes_nothing(self):
        with mock.patch('builtins.input', return_value='no'), self.assertRaises(CommandError):
            self.run_command('--apply')
        self.assertEqual(self.tables(), set())

    def test_apply_replaces_the_tables_and_a_second_run_replaces_them_again(self):
        self.run_command('--apply', '--yes')
        self.assertEqual(self.tables(), {'Browse_by_cell_line', 'Browse_by_animal_studies', 'Browse_by_Patient_Studies', 'Browse_by_index', 'Master'})
        counts = lambda t: pd.read_sql(f'SELECT COUNT(*) n FROM "{t}"', self.engine)['n'][0]
        self.assertEqual((counts('Browse_by_cell_line'), counts('Master')), (3, 5))
        self.run_command('--apply', '--yes')
        self.assertEqual(counts('Browse_by_cell_line'), 3)

    def test_the_current_tables_are_saved_before_they_are_replaced(self):
        self.run_command('--apply', '--yes')
        backup = os.path.join(self.dir.name, 'backup')
        self.run_command('--apply', '--yes', '--backup-dir', backup)
        saved = pd.read_csv(os.path.join(backup, 'Browse_by_cell_line.csv'), dtype=str)
        self.assertEqual(len(saved), 3)

    def test_a_workbook_with_duplicate_ids_is_refused_before_anything_is_written(self):
        write_workbook(self.path, **{'cell line': pd.concat([CELL, CELL.iloc[[0]]])})
        with self.assertRaises(CommandError):
            self.run_command('--apply', '--yes')
        self.assertEqual(self.tables(), set())

    def test_a_workbook_missing_a_sheet_is_refused(self):
        write_workbook(self.path, **{'Patient study': None})
        with self.assertRaises(CommandError):
            self.run_command('--apply', '--yes')

    def test_the_report_file_lists_what_to_fix(self):
        report = os.path.join(self.dir.name, 'report.xlsx')
        self.run_command('--report', report)
        sheets = pd.ExcelFile(report).sheet_names
        self.assertIn('Summary', sheets)
        self.assertIn('Immune term not in the controll', sheets)    # Excel limits sheet names to 31 characters
