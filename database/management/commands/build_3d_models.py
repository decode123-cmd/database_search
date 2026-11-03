import multiprocessing
import os
import shutil
import tempfile

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

from database import importer, tools

SHEETS = {'cell_line': 'Browse_by_cell_line', 'animal_studies': 'Browse_by_animal_studies', 'patient_studies': 'Browse_by_Patient_Studies'}


def embed(smiles, queue):
    """Build one 3D model (RDKit ETKDG embedding, then UFF optimisation, the way the existing models were made) and return its mol block."""
    RDLogger.DisableLog('rdApp.*')
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        queue.put((None, 'SMILES cannot be read'))
        return
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = tools.CONFORMER_SEED
    if AllChem.EmbedMolecule(mol, params) != 0:
        queue.put((None, 'RDKit could not embed it'))
        return
    AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    queue.put((Chem.MolToMolBlock(mol), None))


def build_with_timeout(smiles, seconds):
    """Run embed() in its own process so one stubborn molecule cannot hold everything up."""
    context = multiprocessing.get_context('fork')
    queue = context.Queue()
    process = context.Process(target=embed, args=(smiles, queue))
    process.start()
    process.join(seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return None, f'no result after {seconds} s'
    return queue.get() if not queue.empty() else (None, 'the process ended without a result')


class Command(BaseCommand):
    help = ('Build the 3D models the 3D similarity search uses, for every structure in the data. Models already in the current '
            'workbook are kept; only missing ones are built. Run it after importing new data, then restart the website.')

    def add_arguments(self, parser):
        parser.add_argument('--file', default=None, help='data workbook (default: Final_akshat.xlsx, else Akshat.xlsx)')
        parser.add_argument('--models', default=str(tools.THREED_WORKBOOK), help='the 3D model workbook to extend and replace')
        parser.add_argument('--timeout', type=int, default=30, help='give up on a structure after this many seconds')
        parser.add_argument('--max-heavy-atoms', type=int, default=tools.MAX_QUERY_HEAVY_ATOMS,
                            help='skip structures larger than this (the 3D search rejects larger queries too)')

    def handle(self, *args, **options):
        path = options['file']
        if path is None:
            for candidate in ('Final_akshat.xlsx', 'Akshat.xlsx'):
                if os.path.exists(os.path.join(settings.BASE_DIR, candidate)):
                    path = os.path.join(settings.BASE_DIR, candidate)
                    break
        if not path or not os.path.exists(path):
            raise CommandError('Data workbook not found; give it with --file.')
        RDLogger.DisableLog('rdApp.*')

        tables, _ = importer.read_workbook(path)
        wanted = {study: sorted({s for s in tables[table]['STR_LINK_(SMILES)'].dropna()}) for study, table in SHEETS.items()}

        existing = {}
        models_path = options['models']
        if os.path.exists(models_path):
            for sheet in SHEETS:
                frame = pd.read_excel(models_path, sheet_name=sheet, usecols=['STR_LINK (SMILES)', 'MOL_3D']).dropna()
                for smiles, block in zip(frame['STR_LINK (SMILES)'], frame['MOL_3D']):
                    existing.setdefault(str(smiles).strip(), block)

        built, failed, skipped = {}, [], []
        for study in SHEETS:
            for smiles in wanted[study]:
                if smiles in existing or smiles in built:
                    continue
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue   # not one readable molecule (for example a combination entry): nothing to model
                if mol.GetNumHeavyAtoms() > options['max_heavy_atoms']:
                    skipped.append(smiles)
                    continue
                block, reason = build_with_timeout(smiles, options['timeout'])
                if block:
                    built[smiles] = block
                else:
                    failed.append((smiles, reason))

        rows = {study: [] for study in SHEETS}
        for study in SHEETS:
            for smiles in wanted[study]:
                block = existing.get(smiles) or built.get(smiles)
                if block:
                    rows[study].append({'STR_LINK (SMILES)': smiles, 'MOL_3D': block})

        fd, temporary = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        with pd.ExcelWriter(temporary, engine='openpyxl') as writer:
            for study, entries in rows.items():
                pd.DataFrame(entries, columns=['STR_LINK (SMILES)', 'MOL_3D']).to_excel(writer, sheet_name=study, index=False)
        if os.path.exists(models_path):
            shutil.copyfile(models_path, models_path.replace('.xlsx', '.previous.xlsx'))   # nothing is lost
        shutil.move(temporary, models_path)

        covered = sum(len(v) for v in rows.values())
        total = sum(len(v) for v in wanted.values())
        self.stdout.write(self.style.SUCCESS(f'{covered} of {total} structures (per study type) now have a 3D model: '
                                             f'{len(existing)} existing models available, {len(built)} newly built.'))
        for smiles, reason in failed:
            self.stdout.write(self.style.WARNING(f'  no model: {smiles[:70]} ({reason})'))
        if skipped:
            self.stdout.write(self.style.WARNING(f'  {len(skipped)} structures above {options["max_heavy_atoms"]} heavy atoms were skipped'))
        self.stdout.write('Written to ' + models_path + (' (the previous file is kept next to it)' if os.path.exists(models_path.replace('.xlsx', '.previous.xlsx')) else ''))
