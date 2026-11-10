"""The public page for the articles an AI-assisted literature search suggests for curation (reviewer comment R3-8).

The list is reports/candidate_papers.csv, made by scripts/find_missing_papers.py. These articles are NOT in the
curated database: a curator has to read each one before it is added, and the AI verdicts come from the title and abstract
only. The page says so, and shows the curators' decision for a row as soon as it is filled in the file.
"""
import csv
import os
from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

VERDICTS = {'relevant': 'Likely relevant', 'uncertain': 'Uncertain', 'not_relevant': 'Not relevant'}
STUDY_TYPES = {'cell_line': 'Cell line', 'animal': 'Animal', 'patient': 'Patient', 'mixed': 'Mixed', 'unclear': 'Unclear'}
IN_DATABASE = 'drug_entries_in_database (cell/animal/patient)'
PAGE_SIZE = 25

_cache = {}   # path -> ((modified time, size), rows), so the file is only read again when it changes


def _path():
    return getattr(settings, 'CANDIDATE_PAPERS', os.path.join(settings.BASE_DIR, 'reports', 'candidate_papers.csv'))


def load_rows():
    """The suggested articles, one dict each. A row without a numeric PubMed ID is skipped, so every link is built from an ID."""
    path = _path()
    try:
        stat = os.stat(path)
    except OSError:
        return []
    signature = (stat.st_mtime_ns, stat.st_size)
    if _cache.get(path, (None,))[0] == signature:
        return _cache[path][1]
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for raw in csv.DictReader(handle):
            pmid = (raw.get('pmid') or '').strip()
            if not pmid.isdigit():
                continue
            verdict = (raw.get('ai_verdict') or '').strip()
            study = (raw.get('ai_study_type') or '').strip()
            decision = (raw.get('curator_decision') or '').strip()
            row = {
                'pmid': pmid, 'year': (raw.get('year') or '').strip(), 'journal': (raw.get('journal') or '').strip(),
                'title': (raw.get('title') or '').strip(), 'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
                'verdict': verdict, 'verdict_label': VERDICTS.get(verdict, verdict),
                'study_type': study, 'study_label': STUDY_TYPES.get(study, study),
                'drugs': (raw.get('ai_drugs') or '').strip(), 'cancer_type': (raw.get('ai_cancer_type') or '').strip(),
                'readouts': (raw.get('ai_immune_readouts') or '').strip(), 'reason': (raw.get('ai_reason') or '').strip(),
                'in_database': (raw.get(IN_DATABASE) or '').strip(),
                'status': decision[:1].upper() + decision[1:] if decision else '', 'decided': bool(decision),
            }
            row['search'] = ' '.join([pmid, row['title'], row['journal'], row['drugs'], row['cancer_type']]).lower()
            rows.append(row)
    _cache[path] = (signature, rows)
    return rows


def _number(raw, default=1):
    try:
        return max(int(raw), 1)
    except (TypeError, ValueError):
        return default


def suggested_literature(request):
    rows = load_rows()
    verdict = request.GET.get('verdict', 'relevant')
    if verdict != 'all' and verdict not in VERDICTS:
        verdict = 'relevant'
    year = request.GET.get('year', '')
    study = request.GET.get('study', '') if request.GET.get('study', '') in STUDY_TYPES else ''
    query = request.GET.get('q', '').strip()[:100]

    shown = [r for r in rows
             if (verdict == 'all' or r['verdict'] == verdict) and (not year or r['year'] == year)
             and (not study or r['study_type'] == study) and (not query or query.lower() in r['search'])]
    pages = max(1, -(-len(shown) // PAGE_SIZE))
    page = min(_number(request.GET.get('page')), pages)
    kept = {'verdict': verdict, 'year': year, 'study': study, 'q': query}
    base_query = urlencode({k: v for k, v in kept.items() if v})

    years = sorted({r['year'] for r in rows if r['year']}, reverse=True)
    per_year = [{'year': y, 'screened': sum(1 for r in rows if r['year'] == y),
                 'relevant': sum(1 for r in rows if r['year'] == y and r['verdict'] == 'relevant')} for y in years]
    try:
        updated = datetime.fromtimestamp(os.stat(_path()).st_mtime).strftime('%d %B %Y')
    except OSError:
        updated = ''
    context = {
        'rows': shown[(page - 1) * PAGE_SIZE:page * PAGE_SIZE], 'found': len(shown), 'page': page, 'pages': pages,
        'has_previous': page > 1, 'has_next': page < pages, 'previous_page': page - 1, 'next_page': page + 1,
        'base_query': base_query, 'verdict': verdict, 'year': year, 'study': study, 'query': query,
        'verdicts': VERDICTS, 'study_types': STUDY_TYPES, 'years': years, 'per_year': per_year, 'updated': updated,
        'total': len(rows), 'counts': {key: sum(1 for r in rows if r['verdict'] == key) for key in VERDICTS},
        'accepted': sum(1 for r in rows if r['status'].lower().startswith('accept')),
        'checked': sum(1 for r in rows if r['decided']),
    }
    return render(request, 'database/suggested.html', context)


def download(request):
    """The whole list as a CSV file, exactly as the curators work on it."""
    try:
        with open(_path(), 'rb') as handle:
            data = handle.read()
    except OSError:
        raise Http404('The list of suggested articles is not available.') from None
    response = HttpResponse(data, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="CancerImmunoDB_suggested_literature.csv"'
    return response
