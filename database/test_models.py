import io
import os
import tempfile
from unittest import mock

import pandas as pd
from django.core.management import call_command
from django.test import SimpleTestCase
from rdkit import Chem
from rdkit.Chem import AllChem

from . import tools
from .test_importer import write_workbook


def molblock(smiles):
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    AllChem.EmbedMolecule(mol, randomSeed=1)
    return Chem.MolToMolBlock(mol)


class BuildModelsTests(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.data = os.path.join(self.dir.name, 'data.xlsx')
        self.models = os.path.join(self.dir.name, 'models.xlsx')
        cell = pd.DataFrame({'ID': ['1', '2', '3', '4'], 'Drug': ['a', 'b', 'c', 'd'], 'STR_LINK (SMILES)': ['CCO', 'CCN', 'not a smiles(', 'CCO'],
                             'Drug category': ['x'] * 4, 'Cancer_Type': ['x'] * 4, 'PMID': ['1'] * 4})
        other = cell.iloc[[0]].assign(ID='9')
        write_workbook(self.data, **{'cell line': cell, 'Animal study': other, 'Patient study': other})
        self.reused = molblock('CCO')
        with pd.ExcelWriter(self.models, engine='openpyxl') as writer:
            for sheet in ('cell_line', 'animal_studies', 'patient_studies'):
                pd.DataFrame({'STR_LINK (SMILES)': ['CCO'], 'MOL_3D': [self.reused]}).to_excel(writer, sheet_name=sheet, index=False)

    def build(self):
        out = io.StringIO()
        call_command('build_3d_models', '--file', self.data, '--models', self.models, '--timeout', '60', stdout=out)
        return out.getvalue()

    def test_existing_models_are_kept_and_missing_ones_built(self):
        text = self.build()
        self.assertIn('1 newly built', text)
        frame = pd.read_excel(self.models, sheet_name='cell_line')
        blocks = dict(zip(frame['STR_LINK (SMILES)'], frame['MOL_3D']))
        self.assertEqual(blocks['CCO'], self.reused)                    # not rebuilt
        self.assertIn('CCN', blocks)                                   # built
        self.assertNotIn('not a smiles(', blocks)                       # nothing to model

    def test_the_previous_file_is_kept(self):
        self.build()
        self.assertTrue(os.path.exists(self.models.replace('.xlsx', '.previous.xlsx')))

    def test_the_search_can_read_what_was_built(self):
        self.build()
        with mock.patch.object(tools, 'THREED_WORKBOOK', self.models):
            tools._workbook_models.cache_clear()
            self.addCleanup(tools._workbook_models.cache_clear)
            models = tools._workbook_models()
        self.assertEqual(set(models), {'CCO', 'CCN'})
        self.assertGreater(models['CCN'].GetNumConformers(), 0)

    def test_running_it_twice_builds_nothing_new(self):
        self.build()
        self.assertIn('0 newly built', self.build())
