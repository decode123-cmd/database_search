# CancerImmunoDB

A manually curated database of the immunomodulatory effects of anticancer drugs (Django, PostgreSQL, RDKit).

## Updating the data

The website reads four tables made from the curated workbook (sheets `cell line`, `Animal study`, `Patient study` and
`Browse by index`). To publish a new version of the workbook:

1. **Check it.** Nothing is written and no database is contacted:

   `python manage.py import_excel --file Final_akshat.xlsx --report reports/Data_QA_report.xlsx`

   The report lists what to fix: values outside the index lists, controlled terms missing from the lists, sex ratios that
   Excel turned into dates, duplicate IDs, and text in columns without a heading.
2. **Replace the website tables.** The command shows which database it is about to replace and asks for confirmation. All
   tables are replaced in one transaction, so either all of them change or none does. `--backup-dir` first saves the
   current tables as CSV files.

   `python manage.py import_excel --file Final_akshat.xlsx --apply --backup-dir backups/2026-11-03`
3. **Rebuild what is derived from the data:**
   - `python manage.py build_3d_models --file Final_akshat.xlsx` (3D models for the 3D similarity search; existing ones are kept)
   - `python scripts/make_stats_charts.py` (the statistics charts)
   - `python scripts/make_architecture_figure.py` (the counts in the architecture figure)
4. **Restart the website.**

The command uses the database in `DATABASES['default']`, so the import and the website cannot disagree about where the data
lives. **If `DATABASE_URL` is not set, that is the database written in `settings.py`, which is the live site's.** To try an
import first, point `DATABASE_URL` at a copy (for example `DATABASE_URL=sqlite:///test.sqlite3`). `--apply` always prints the
database it is about to replace and waits for you to type `yes`.

## Other tools

- `python manage.py check_coverage --drug NAME --pmid ID` (or `--file list.csv`) shows whether drugs or articles are already in the database.
- `python scripts/publication_years.py` looks up the publication year of every article in the data.
- `benchmarks/benchmark_tools.py` compares the structure searches with Open Babel (results in `benchmarks/RESULTS.md`).
- `python manage.py test database` runs the tests. They never open a database connection.

## API

A read-only REST API is documented on the site under Information, Download & API (`/api/v1/`).
