import csv
import sys

from django.core.management.base import BaseCommand, CommandError

from database.api import _study_frame
from database.coverage import STUDY_TYPES, check_candidates


class Command(BaseCommand):
    help = ('Report whether drugs or PubMed IDs are already in the database, per study type. '
            'Use it to sort a list of suggested entries (from PubMed, Claude, Gemini ...) into "already there" and "missing" before curating.')

    def add_arguments(self, parser):
        parser.add_argument('--drug', action='append', default=[], help='drug name to look for (repeat for several)')
        parser.add_argument('--pmid', action='append', default=[], help='PubMed ID to look for (repeat for several)')
        parser.add_argument('--file', help='CSV file with a "drug" and/or a "pmid" column')
        parser.add_argument('--csv', action='store_true', help='print CSV instead of a table')

    def handle(self, *args, **options):
        drugs, pmids = list(options['drug']), list(options['pmid'])
        if options['file']:
            with open(options['file'], newline='', encoding='utf-8-sig') as handle:
                for row in csv.DictReader(handle):
                    row = {(k or '').strip().lower(): (v or '').strip() for k, v in row.items()}
                    if row.get('drug'):
                        drugs.append(row['drug'])
                    if row.get('pmid'):
                        pmids.append(row['pmid'])
        if not drugs and not pmids:
            raise CommandError('Give at least one --drug, --pmid or --file.')

        frames = {study: _study_frame(study) for study in STUDY_TYPES}
        rows = check_candidates(frames, drugs, pmids)

        header = ['kind', 'query', *STUDY_TYPES, 'status']
        if options['csv']:
            writer = csv.writer(self.stdout, lineterminator='\n')
            writer.writerow(header)
            writer.writerows([[row[column] for column in header] for row in rows])
            return
        widths = [max(len(str(row[column])) for row in rows + [dict(zip(header, header))]) for column in header]
        for line in [dict(zip(header, header))] + rows:
            self.stdout.write('  '.join(str(line[column]).ljust(width) for column, width in zip(header, widths)).rstrip())
