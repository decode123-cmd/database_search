"""Counts behind the Browse pages: how many studies fall under each drug category, cancer type, technique and immune term.

A drug category is a single value per study and is matched exactly (ignoring case and spacing), so a study is counted
once. Cancer types, techniques and immune terms can be lists separated by semicolons, and a study is counted under every
term it lists. Only the terms in the index lists get a row; the studies that match none of
them are counted separately, so nothing is hidden.
"""
import pandas as pd
from django.db import connection

from .importer import CONTROLLED_COLUMNS, IMMUNE_OUTCOMES, norm, split_terms

COUNT_TABLES = {
    'Cell_Count': 'Browse_by_cell_line',
    'Animal_Count': 'Browse_by_animal_studies',
    'Patient_Count': 'Browse_by_Patient_Studies',
}
INDEX_TABLE = 'Browse_by_index'
FIELD_TABLES = {key.lower(): table for key, table in COUNT_TABLES.items()}   # cell_count -> Browse_by_cell_line, as used in the links

BROWSE_KINDS = {
    'drug_category': {'column': 'Drug_category', 'list': 'Drug_category', 'terms': False},
    'cancer_type': {'column': 'Cancer_Type', 'list': 'Cancer_Type', 'terms': True},   # a few studies list several, separated by semicolons
    'technique': {'column': CONTROLLED_COLUMNS['technique'], 'list': 'Controlled_Technique', 'terms': True},
    'immune': {'column': None, 'list': 'Controlled_Immune_Term', 'terms': True},
}
OUTCOMES = ('any',) + IMMUNE_OUTCOMES


def _read(table):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM "{table}"')
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def _columns_for(kind, outcome='any'):
    if kind not in BROWSE_KINDS:
        raise ValueError('Invalid browse kind')
    if kind != 'immune':
        return [BROWSE_KINDS[kind]['column']]
    if outcome == 'any':
        return [CONTROLLED_COLUMNS[o] for o in IMMUNE_OUTCOMES]
    if outcome in IMMUNE_OUTCOMES:
        return [CONTROLLED_COLUMNS[outcome]]
    raise ValueError('Invalid outcome')


def _row_terms(df, columns, terms):
    """For every study, the set of normalised values it has in `columns` (split on semicolons for term columns)."""
    present = [c for c in columns if c in df.columns]
    out = []
    for values in zip(*(df[c] for c in present)) if present else ((),) * len(df):
        found = set()
        for value in values:
            if terms:
                found.update(norm(t) for t in split_terms(value))
            elif value is not None and norm(value):
                found.add(norm(value))
        out.append(found)
    return out


def browse(kind, outcome='any'):
    """Counts for one Browse page.

    Returns {'table': {name: {Cell_Count, Animal_Count, Patient_Count}}, 'totals': {...}, 'unassigned': {...}} where
    'unassigned' counts the studies that appear in no row of the table. Term pages also return 'mentions' and 'listed'
    (how many term mentions there are, and how many of them are in the list). If the data has not been imported with
    the controlled terms yet, 'table' is empty and 'missing' names what is absent."""
    _columns_for(kind, outcome)   # rejects an unknown kind or outcome before anything is read
    studies = {key: _read(table) for key, table in COUNT_TABLES.items()}
    return browse_frames(studies, _read(INDEX_TABLE), kind, outcome)


def browse_frames(studies, index, kind, outcome='any'):
    """browse() on tables already in memory (also used to draw the charts straight from the workbook)."""
    columns = _columns_for(kind, outcome)
    spec = BROWSE_KINDS[kind]
    if spec['list'] not in index.columns or not any(c in df.columns for df in studies.values() for c in columns):
        return {'table': {}, 'totals': {}, 'unassigned': {}, 'missing': spec['list']}

    names, seen = [], set()
    for value in index[spec['list']]:
        if value is not None and norm(value) and norm(value) not in seen:
            seen.add(norm(value))
            names.append(str(value).strip())
    wanted = {norm(n): n for n in names}

    table = {n: {key: 0 for key in COUNT_TABLES} for n in names}
    totals = {key: len(df) for key, df in studies.items()}
    unassigned = {key: 0 for key in COUNT_TABLES}
    mentions = listed = 0
    for key, df in studies.items():
        for found in _row_terms(df, columns, spec['terms']):
            hits = [t for t in found if t in wanted]
            for t in hits:
                table[wanted[t]][key] += 1
            if not hits:
                unassigned[key] += 1
            mentions += len(found)
            listed += len(hits)
    result = {'table': table, 'totals': totals, 'unassigned': unassigned}
    if spec['terms']:
        result.update({'mentions': mentions, 'listed': listed})
    return result


def studies_with(kind, field, term, outcome='any'):
    """The studies behind one count: every study of the given type whose value, or list of terms, includes `term`."""
    if field not in FIELD_TABLES:
        raise ValueError('Invalid field specified')
    columns = _columns_for(kind, outcome)
    df = _read(FIELD_TABLES[field])
    wanted = norm(term)
    mask = [wanted in found for found in _row_terms(df, columns, BROWSE_KINDS[kind]['terms'])]
    return df[mask]


def data_get(field):
    query_map = {'cell_count': 'Browse_by_cell_line', 'animal_count': 'Browse_by_animal_studies', 'patient_count': 'Browse_by_Patient_Studies'}
    if field not in query_map:
        raise ValueError("Invalid field specified")
    df = _read(query_map[field])
    return df, list(df.columns)
