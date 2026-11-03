import os
from urllib.parse import quote_plus

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from database import importer


def database_engine():
    """SQLAlchemy engine for the database the website itself uses (DATABASES['default']), so the import and the site cannot disagree."""
    from sqlalchemy import create_engine
    db = settings.DATABASES['default']
    backend = db['ENGINE']
    if backend.endswith('sqlite3'):
        return create_engine(f"sqlite:///{db['NAME']}")
    if 'postgresql' in backend:
        user, password = quote_plus(db.get('USER') or ''), quote_plus(db.get('PASSWORD') or '')
        auth = f'{user}:{password}@' if user else ''
        port = f":{db['PORT']}" if db.get('PORT') else ''
        return create_engine(f"postgresql+psycopg2://{auth}{db.get('HOST') or 'localhost'}{port}/{db['NAME']}")
    raise CommandError(f'Unsupported database engine: {backend}')


def write_report(path, lines, report):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        pd.DataFrame({'Summary': lines}).to_excel(writer, sheet_name='Summary', index=False)
        for title, rows in report['worklists'].items():
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name=title[:31], index=False)
        for kind, c in report.get('coverage', {}).items():
            if c['list_never_used']:
                pd.DataFrame({f'{kind} list entries never used in the data': c['list_never_used']}).to_excel(
                    writer, sheet_name=f'Unused {kind} list entries'[:31], index=False)


class Command(BaseCommand):
    help = ('Check the curated workbook and, only with --apply, replace the website tables with it. '
            'Without --apply nothing is written and no database is contacted.')

    def add_arguments(self, parser):
        parser.add_argument('--file', default=None, help='workbook to read (default: Final_akshat.xlsx, else Akshat.xlsx, in the project folder)')
        parser.add_argument('--report', help='write the checks and the lists of things to fix to this .xlsx file')
        parser.add_argument('--apply', action='store_true', help='replace the tables in the website database')
        parser.add_argument('--yes', action='store_true', help='do not ask for confirmation (with --apply)')
        parser.add_argument('--backup-dir', help='save the current tables as CSV files in this folder before replacing them')

    def handle(self, *args, **options):
        path = options['file']
        if path is None:
            for candidate in ('Final_akshat.xlsx', 'Akshat.xlsx'):
                if os.path.exists(os.path.join(settings.BASE_DIR, candidate)):
                    path = os.path.join(settings.BASE_DIR, candidate)
                    break
        if not path or not os.path.exists(path):
            raise CommandError('Workbook not found; give it with --file.')

        self.stdout.write(f'Reading {path}')
        tables, notes = importer.read_workbook(path)
        report = importer.check(tables)
        lines = importer.summarise(tables, notes, report)
        for line in lines:
            self.stdout.write(line)
        if options['report']:
            write_report(options['report'], lines, report)
            self.stdout.write(self.style.SUCCESS(f"Report written to {options['report']}"))

        problems = []
        if notes['missing_sheets']:
            problems.append(f"missing sheets: {notes['missing_sheets']}")
        for study, info in report['tables'].items():
            if info['duplicate_ids']:
                problems.append(f'{study} has duplicate IDs')
            if info['blank_ids']:
                problems.append(f'{study} has rows without an ID')
        if problems:
            raise CommandError('Not safe to import: ' + '; '.join(problems))

        if not options['apply']:
            self.stdout.write(self.style.WARNING('Dry run: nothing was written. Add --apply to replace the website tables.'))
            return

        engine = database_engine()
        target = engine.url.render_as_string(hide_password=True)
        self.stdout.write(self.style.WARNING(f'This replaces {", ".join(tables)} in: {target}'))
        if not options['yes'] and input('Type "yes" to continue: ').strip().lower() != 'yes':
            raise CommandError('Cancelled; nothing was written.')

        if options['backup_dir']:
            os.makedirs(options['backup_dir'], exist_ok=True)
            for name in tables:
                try:
                    current = pd.read_sql(f'SELECT * FROM "{name}"', engine)
                except Exception:
                    continue   # the table does not exist yet
                current.to_csv(os.path.join(options['backup_dir'], f'{name}.csv'), index=False)
                self.stdout.write(f'  backed up {name}: {len(current)} rows')

        with engine.begin() as connection:   # one transaction: either every table is replaced or none is
            for name, frame in tables.items():
                frame.to_sql(name, connection, if_exists='replace', index=False)
        with engine.connect() as connection:
            for name, frame in tables.items():
                count = pd.read_sql(f'SELECT COUNT(*) AS n FROM "{name}"', connection)['n'][0]
                if count != len(frame):
                    raise CommandError(f'{name}: wrote {len(frame)} rows but the database holds {count}')
                self.stdout.write(self.style.SUCCESS(f'  {name}: {count} rows'))
        self.stdout.write(self.style.SUCCESS('Import finished. Restart the website so it picks up the new data.'))
