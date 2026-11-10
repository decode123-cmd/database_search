"""Find recent articles the database may be missing (reviewer comment R3-8) and write a list for the curators to check.

Why this is built the way it is:
  * Every PubMed ID comes from PubMed itself (NCBI E-utilities). The AI never supplies an ID: language models invent
    plausible-looking IDs and titles, so a list of references written by an AI cannot be trusted.
  * The AI (Gemini) only reads the title and abstract that PubMed returned and answers the same question a curator would:
    does the article test a named anticancer drug and measure its effect on the immune system?
  * It judges from the abstract alone, so every row it marks is a suggestion. A curator must read the full text (the
    database records doses, techniques and immune terms that abstracts often omit) and fill in `curator_decision`.
  * Nothing is written to the database or the workbook.

Only public PubMed titles and abstracts leave this machine (to NCBI, and to Google when a key is set). The key is read
from the environment and is never stored:

    export GEMINI_API_KEY=...        # optional; without it the list is made without the AI verdict
    python scripts/find_missing_papers.py --years 2021-2025 --per-year 100 --validate 40

Needs pandas and openpyxl (it reads Final_akshat.xlsx) and the project's `database` package.
"""
import argparse
import csv
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from database import importer  # noqa: E402
from database.coverage import STUDY_TYPES, check_candidates  # noqa: E402

EUTILS = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
GEMINI = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

SCOPE = (
    '(neoplasms[MeSH Terms] OR cancer[Title/Abstract] OR tumor[Title/Abstract] OR tumour[Title/Abstract]) '
    'AND ("antineoplastic agents"[MeSH Terms] OR "drug therapy"[Subheading] OR "immune checkpoint inhibitors"[MeSH Terms] '
    'OR chemotherapy[Title/Abstract] OR inhibitor[Title/Abstract]) '
    'AND (immunomodulat*[Title/Abstract] OR "antigen presentation"[Title/Abstract] OR "MHC class I"[Title/Abstract] '
    'OR "PD-L1"[Title/Abstract] OR "NK cells"[Title/Abstract] OR "T cell"[Title/Abstract] '
    'OR "immunogenic cell death"[Title/Abstract] OR "tumor microenvironment"[Title/Abstract] '
    'OR "immune response"[Title/Abstract]) '
    'AND hasabstract AND English[lang] AND journal article[pt] NOT review[pt]'
)
# Papers that are about cancer but not about drugs changing the immune system, to check the AI says "no" to them.
NEGATIVE = ('neoplasms[MeSH Terms] AND (epidemiology[Subheading] OR surgery[Subheading] OR diagnosis[Subheading]) '
            'NOT immun*[Title/Abstract] AND hasabstract AND English[lang] AND journal article[pt] NOT review[pt]')

CRITERIA = """You are screening PubMed articles for CancerImmunoDB, a manually curated database of the immunomodulatory
effects of anticancer drugs.

An article is "relevant" only if ALL of these hold:
1. It experimentally tests one or more named anticancer drugs or agents (chemotherapy, targeted drugs, checkpoint
   antibodies, immunomodulatory drugs, epigenetic drugs and so on) as treatment of cancer cell lines, tumour-bearing
   animals or cancer patients.
2. It reports a measured effect of that treatment on the immune system or on an immune-related tumour feature
   (immune cell numbers or function, cytokines, antigen presentation or MHC, immune checkpoint expression, NK or T cell
   recognition, immunogenic cell death and similar).
3. It is primary research: not a review, meta-analysis, editorial, protocol or case report.

Not relevant: only survival, response or safety outcomes; prognostic biomarkers without a drug being tested; cell
therapies or vaccines where no drug effect on the immune system is measured.

Use ONLY the text given for each article. Do not add facts from memory. If the abstract is too vague to decide, answer
"uncertain". Copy each pmid exactly as given. Answer in the JSON format requested."""

SCHEMA = {
    'type': 'ARRAY',
    'items': {
        'type': 'OBJECT',
        'properties': {
            'pmid': {'type': 'STRING'},
            'verdict': {'type': 'STRING', 'enum': ['relevant', 'uncertain', 'not_relevant']},
            'study_type': {'type': 'STRING', 'enum': ['cell_line', 'animal', 'patient', 'mixed', 'unclear']},
            'drugs': {'type': 'ARRAY', 'items': {'type': 'STRING'}},
            'cancer_type': {'type': 'STRING'},
            'immune_readouts': {'type': 'STRING'},
            'reason': {'type': 'STRING'},
        },
        'required': ['pmid', 'verdict', 'study_type', 'drugs', 'cancer_type', 'immune_readouts', 'reason'],
    },
}


def post(url, fields, headers=None, timeout=90):
    request = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def search(term, retmax):
    fields = {'db': 'pubmed', 'term': term, 'retmax': retmax, 'sort': 'relevance', 'retmode': 'json', 'tool': 'cancerimmunodb'}
    time.sleep(0.4)
    return json.loads(post(EUTILS + 'esearch.fcgi', fields))['esearchresult']['idlist']


def fetch_articles(pmids):
    """PubMed ID -> {title, abstract, year, journal, doi}, read from the PubMed record itself."""
    articles = {}
    for start in range(0, len(pmids), 100):
        batch = pmids[start:start + 100]
        time.sleep(0.4)
        root = ET.fromstring(post(EUTILS + 'efetch.fcgi', {'db': 'pubmed', 'id': ','.join(batch), 'retmode': 'xml', 'tool': 'cancerimmunodb'}))
        for node in root.iter('PubmedArticle'):
            pmid = node.findtext('.//MedlineCitation/PMID')
            parts = []
            for text in node.findall('.//Abstract/AbstractText'):
                label = text.get('Label')
                body = ''.join(text.itertext()).strip()
                parts.append(f'{label}: {body}' if label else body)
            year = node.findtext('.//JournalIssue/PubDate/Year') or (node.findtext('.//JournalIssue/PubDate/MedlineDate') or '')[:4]
            doi = next((i.text for i in node.findall('.//ArticleIdList/ArticleId') if i.get('IdType') == 'doi'), '')
            articles[pmid] = {'title': ''.join(node.find('.//ArticleTitle').itertext()).strip() if node.find('.//ArticleTitle') is not None else '',
                              'abstract': ' '.join(parts), 'year': year, 'doi': doi or '',
                              'journal': node.findtext('.//Journal/Title') or ''}
    return articles


def ask_gemini(key, model, articles):
    """One request for several articles. Returns pmid -> answer; an ID the AI returns that was not asked for is ignored."""
    listing = '\n\n'.join(f'pmid: {pmid}\ntitle: {a["title"]}\nabstract: {a["abstract"][:3500]}' for pmid, a in articles.items())
    body = {'contents': [{'parts': [{'text': CRITERIA + '\n\nARTICLES:\n\n' + listing}]}],
            'generationConfig': {'temperature': 0, 'responseMimeType': 'application/json', 'responseSchema': SCHEMA}}
    request = urllib.request.Request(GEMINI.format(model=model), data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                text = json.load(response)['candidates'][0]['content']['parts'][0]['text']
            return {str(item['pmid']): item for item in json.loads(text) if str(item.get('pmid')) in articles}
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', 'replace')
            if error.code not in (429, 500, 503) or 'PerDay' in detail or 'per day' in detail:
                hint = ' (daily limit: wait, use another model or a paid key)' if error.code == 429 else ''
                raise RuntimeError(f'Gemini returned HTTP {error.code}{hint}: {" ".join(detail.split())[:300]}') from None
            time.sleep(20 * (attempt + 1))   # the free tier allows only a few requests a minute
        except (TimeoutError, urllib.error.URLError, KeyError, IndexError, ValueError):   # a stalled request or an unreadable answer: try again
            time.sleep(5)
    return {}


def screen(key, model, articles, size):
    answers = {}
    pmids = list(articles)
    for start in range(0, len(pmids), size):
        chunk = {p: articles[p] for p in pmids[start:start + size]}
        try:
            answers.update(ask_gemini(key, model, chunk))
        except RuntimeError as error:   # e.g. the daily limit: keep what is done, mark the rest "no answer"
            print(f'  STOPPED: {error}', flush=True)
            break
        print(f'  screened {min(start + size, len(pmids))}/{len(pmids)}', flush=True)
        time.sleep(7)
    return answers


def database_frames(tables):
    return {'cell_line': tables['Browse_by_cell_line'], 'animal_studies': tables['Browse_by_animal_studies'],
            'patient_studies': tables['Browse_by_Patient_Studies']}


def in_database(frames, drugs):
    """e.g. 'Pomalidomide 31/9/4 (cell/animal/patient)' for every drug the AI named."""
    out = []
    for row in check_candidates(frames, drugs=[d for d in drugs if d.strip()][:4]):
        out.append(f'{row["query"]} {row["cell_line"]}/{row["animal_studies"]}/{row["patient_studies"]}')
    return '; '.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--file', default=os.path.join(ROOT, 'Final_akshat.xlsx'))
    parser.add_argument('--years', default='2021-2025', help='first-last publication year, e.g. 2021-2025')
    parser.add_argument('--per-year', type=int, default=100, help='how many of the best PubMed matches to look at per year')
    parser.add_argument('--validate', type=int, default=40, help='also test the AI on this many papers already in the database (0 = skip)')
    parser.add_argument('--model', default='gemini-3.5-flash')
    parser.add_argument('--batch', type=int, default=8, help='articles per AI request')
    parser.add_argument('--out', default=os.path.join(ROOT, 'reports', 'candidate_papers.csv'))
    args = parser.parse_args()
    key = os.environ.get('GEMINI_API_KEY')
    first, last = (int(x) for x in args.years.split('-'))

    tables, _ = importer.read_workbook(args.file)
    frames = database_frames(tables)
    have = {str(p).strip()[:-2] if str(p).endswith('.0') else str(p).strip()
            for table in frames.values() for p in table['PMID'].dropna()}
    print(f'{len(have)} PubMed IDs already in the database')

    if key and args.validate:
        print('Checking the AI against papers a curator already accepted, and against unrelated cancer papers ...')
        known = random.Random(1).sample(sorted(p for p in have if p.isdigit()), args.validate)
        unrelated = search(f'{NEGATIVE} AND {first}:{last}[dp]', 200)
        unrelated = random.Random(1).sample(unrelated, min(20, len(unrelated)))
        sample = fetch_articles(known + unrelated)
        sample = {p: a for p, a in sample.items() if a['abstract']}
        result = screen(key, args.model, sample, args.batch)
        for label, ids in (('already in the database', known), ('unrelated cancer papers', unrelated)):
            ids = [p for p in ids if p in sample]
            tally = {v: sum(1 for p in ids if result.get(p, {}).get('verdict') == v) for v in ('relevant', 'uncertain', 'not_relevant')}
            tally['no answer'] = sum(1 for p in ids if p not in result)
            print(f'  {label} ({len(ids)} with an abstract): {tally}')

    rows, per_year, seen = [], {}, set()
    for year in range(last, first - 1, -1):
        hits = search(f'({SCOPE}) AND {year}[dp]', args.per_year)
        new = [p for p in hits if p not in have and p not in seen]   # an article online in one year and in print in the next matches both
        seen.update(new)
        per_year[year] = (len(hits), len([p for p in hits if p in have]))
        print(f'{year}: {len(hits)} best PubMed matches, {per_year[year][1]} already in the database, {len(new)} to check')
        articles = {p: a for p, a in fetch_articles(new).items() if a['abstract']}
        answers = screen(key, args.model, articles, args.batch) if key else {}
        for pmid, article in articles.items():
            answer = answers.get(pmid, {})
            drugs = answer.get('drugs') or []
            rows.append({
                'pmid': pmid, 'year': article['year'], 'journal': article['journal'], 'title': article['title'],
                'pubmed_url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
                'ai_verdict': answer.get('verdict', 'not screened' if not key else 'no answer'),
                'ai_study_type': answer.get('study_type', ''), 'ai_drugs': '; '.join(drugs),
                'ai_cancer_type': answer.get('cancer_type', ''), 'ai_immune_readouts': answer.get('immune_readouts', ''),
                'ai_reason': answer.get('reason', ''),
                'drug_entries_in_database (cell/animal/patient)': in_database(frames, drugs),
                'curator_decision': '', 'curator_notes': '',
            })

    order = {'relevant': 0, 'uncertain': 1, 'no answer': 2, 'not screened': 2, 'not_relevant': 3}
    rows.sort(key=lambda r: (order[r['ai_verdict']], -int(r['year'] or 0), r['pmid']))
    if key and all(r['ai_verdict'] == 'no answer' for r in rows):
        sys.exit('The AI answered none of the articles, so nothing was written (an earlier report, if any, is untouched).')
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'\nWrote {len(rows)} articles to {args.out}')
    for verdict in ('relevant', 'uncertain', 'not_relevant', 'no answer', 'not screened'):
        print(f'  {verdict}: {sum(1 for r in rows if r["ai_verdict"] == verdict)}')
    print('  per year (best matches / already in database):', ', '.join(f'{y}: {a}/{b}' for y, (a, b) in sorted(per_year.items())))


if __name__ == '__main__':
    main()
