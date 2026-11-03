"""Find the publication year of every article the database draws on (reviewer comment R3-8: which years are covered?).

Only the PubMed IDs are sent, to NCBI's public E-utilities. Needs pandas and openpyxl (to read the workbook):

    python scripts/publication_years.py [--file Final_akshat.xlsx] [--out reports/publication_years.csv]
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from database import importer  # noqa: E402

ESUMMARY = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
BATCH = 150


def fetch_years(pmids):
    years = {}
    for start in range(0, len(pmids), BATCH):
        batch = pmids[start:start + BATCH]
        data = urllib.parse.urlencode({'db': 'pubmed', 'id': ','.join(batch), 'retmode': 'json', 'tool': 'cancerimmunodb'}).encode()
        with urllib.request.urlopen(urllib.request.Request(ESUMMARY, data=data), timeout=60) as response:
            result = json.load(response)['result']
        for pmid in batch:
            entry = result.get(pmid)
            text = (entry or {}).get('sortpubdate') or (entry or {}).get('pubdate') or ''
            if text[:4].isdigit():
                years[pmid] = int(text[:4])
        time.sleep(0.4)   # stay under NCBI's limit of 3 requests a second
    return years


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--file', default=os.path.join(ROOT, 'Final_akshat.xlsx'))
    parser.add_argument('--out', default=os.path.join(ROOT, 'reports', 'publication_years.csv'))
    args = parser.parse_args()
    tables, _ = importer.read_workbook(args.file)
    by_study = {}
    for study, name in importer.STUDY_TABLES.items():
        by_study[study] = [p for p in tables[name]['PMID'].dropna().astype(str)]
    pmids = sorted({p for values in by_study.values() for p in values if p.isdigit()})
    print(f'{len(pmids)} distinct PubMed IDs in the data')
    years = fetch_years(pmids)
    print(f'{len(years)} found in PubMed; {len(pmids) - len(years)} not found')

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['PMID', 'publication_year'])
        for pmid in pmids:
            writer.writerow([pmid, years.get(pmid, '')])

    values = sorted(years.values())
    print(f'Publication years: {values[0]} to {values[-1]}; median {values[len(values) // 2]}')
    counts = Counter(values)
    print('articles per year:', ', '.join(f'{y}: {counts[y]}' for y in sorted(counts)))
    for study, ids in by_study.items():
        studied = [years[p] for p in ids if p in years]
        print(f'{study}: {len(studied)} studies with a known year, {min(studied)} to {max(studied)}')
    last = max(values)
    print(f'share of articles published in {last - 4} or later: {sum(1 for v in values if v >= last - 4) / len(values):.0%}')


if __name__ == '__main__':
    main()
