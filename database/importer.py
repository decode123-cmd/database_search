"""Turn the curated workbook into the tables the website reads, and check it on the way.

The workbook has one sheet per study type plus an index sheet with the lists used to build the Browse pages.
This module only reads and checks; `manage.py import_excel` writes the result to the database.
"""
import re

import pandas as pd

STUDY_TABLES = {
    'cell_line': 'Browse_by_cell_line',
    'animal_studies': 'Browse_by_animal_studies',
    'patient_studies': 'Browse_by_Patient_Studies',
}
INDEX_TABLE = 'Browse_by_index'
MASTER_TABLE = 'Master'

# sheet names accepted for each study type (compared without case and extra spaces), so the workbook can be
# named the old way ("Browse by cell line") or the new way ("cell line")
SHEET_ALIASES = {
    'cell_line': {'cell line', 'browse by cell line'},
    'animal_studies': {'animal study', 'animal studies', 'browse by animal studies'},
    'patient_studies': {'patient study', 'patient studies', 'browse by patient studies'},
}
INDEX_ALIASES = {'browse by index'}

CONTROLLED_COLUMNS = {
    'technique': 'Controlled_Technique',
    'enhanced': 'Controlled_Terms_Function_enhanced_Number_increased',
    'inhibited': 'Controlled_Terms_Function_inhibited_Number_decreased',
    'unaffected': 'Controlled_Terms_Unaffected',
    'negative': 'Controlled_Terms_Negative_Regulation',
}
IMMUNE_OUTCOMES = ('enhanced', 'inhibited', 'unaffected', 'negative')   # the four controlled immune columns
ID_COLUMNS = ('PMID', 'Pubchem_ID', 'Drug_Pubchem')                      # numbers that must not carry a ".0"
MAX_COLUMN_LENGTH = 63                                                   # PostgreSQL's identifier limit


def _key(name):
    return re.sub(r'\s+', ' ', str(name)).strip().lower()


def table_column(name):
    """Column name as the old importer made it (spaces become underscores), with the controlled columns given one spelling in every table."""
    plain = re.sub(r'\s+', ' ', str(name)).strip().lower().replace('_', ' ')
    if plain.startswith('controlled technique'):
        return CONTROLLED_COLUMNS['technique']
    if plain.startswith('controlled terms'):
        for outcome, marker in (('enhanced', 'enha'), ('inhibited', 'inhibit'), ('unaffected', 'unaffected'), ('negative', 'negative')):
            if marker in plain:
                return CONTROLLED_COLUMNS[outcome]
    return str(name).strip().replace(' ', '_')[:MAX_COLUMN_LENGTH]


def split_terms(value):
    """The terms of a controlled cell: they are separated by semicolons."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [term.strip() for term in str(value).split(';') if term.strip()]


def norm(value):
    return re.sub(r'\s+', ' ', str(value)).strip().lower() if pd.notna(value) else ''


def _clean(df, notes, sheet):
    """Trim text, turn blanks into missing values, and remove the ".0" Excel adds to identifiers. Nothing else is changed."""
    out = df.copy()
    for column in out.columns:
        out[column] = out[column].map(lambda v: v.strip() if isinstance(v, str) else v)
        out[column] = out[column].replace('', pd.NA)
    fixed = {}
    for column in ID_COLUMNS:
        if column in out.columns:
            before = out[column].astype('string')
            after = before.str.replace(r'^(\d+)\.0$', r'\1', regex=True)
            fixed[column] = int((before != after).sum())
            out[column] = after
    notes['id_fixes'][sheet] = {c: n for c, n in fixed.items() if n}
    return out.astype(object).where(out.notna(), None)


def find_sheet(workbook, aliases):
    for name in workbook.sheet_names:
        if _key(name) in aliases:
            return name
    return None


def read_workbook(path):
    """Read the workbook. Returns (tables, notes): tables maps table name -> DataFrame; notes holds what was changed or left out."""
    workbook = pd.ExcelFile(path)
    notes = {'sheets': {}, 'dropped_notes': [], 'id_fixes': {}, 'missing_sheets': []}
    tables = {}
    for study, aliases in SHEET_ALIASES.items():
        sheet = find_sheet(workbook, aliases)
        if sheet is None:
            notes['missing_sheets'].append(study)
            continue
        raw = workbook.parse(sheet, dtype=str).dropna(how='all')
        keep = []
        for column in raw.columns:
            if str(column).startswith('Unnamed'):
                filled = int(raw[column].notna().sum())
                if filled:
                    notes['dropped_notes'].append({'sheet': sheet, 'column': str(column), 'rows_with_text': filled,
                                                   'example': str(raw[column].dropna().iloc[0])[:120]})
                continue
            keep.append(column)
        data = raw[keep].copy()
        names = [table_column(c) for c in data.columns]
        duplicated = sorted({n for n in names if names.count(n) > 1})
        if duplicated:
            raise ValueError(f"Sheet '{sheet}' has columns that end up with the same name: {duplicated}")
        data.columns = names
        tables[STUDY_TABLES[study]] = _clean(data, notes, sheet)
        notes['sheets'][sheet] = STUDY_TABLES[study]

    index_sheet = find_sheet(workbook, INDEX_ALIASES)
    if index_sheet is None:
        notes['missing_sheets'].append('index')
    else:
        tables[INDEX_TABLE] = read_index(workbook.parse(index_sheet, dtype=str))
        notes['sheets'][index_sheet] = INDEX_TABLE

    studies = []
    for study, table in STUDY_TABLES.items():
        if table in tables:
            frame = tables[table].copy()
            frame.insert(1, 'Study_type', study)
            studies.append(frame)
    if studies:
        tables[MASTER_TABLE] = pd.concat(studies, ignore_index=True, sort=False)
    return tables, notes


def read_index(raw):
    """The index sheet holds side-by-side lists. Return them as columns of one tidy table, each list without blanks or repeats."""
    def values(*names):
        for name in names:
            if name in raw.columns:
                seen, out = set(), []
                for value in raw[name].dropna().astype(str):
                    text = re.sub(r'\s+', ' ', value).strip()
                    if text and text.lower() not in seen:
                        seen.add(text.lower())
                        out.append(text)
                return out
        return []

    old_style = 'Drug_category' in raw.columns   # the previous workbook had a clean "Drug_category" list next to the counts
    lists = {
        'Drug_category': values('Drug_category' if old_style else 'Drug category1', 'Drug category1', 'Drug_category'),
        'Cancer_Type': values('Cancer_Type'),
        'Controlled_Technique': values('Controlled word'),
        'Controlled_Immune_Term': values('Controlled word.1'),
    }
    if not lists['Controlled_Technique'] and 'Technique' in raw.columns:
        lists['Technique'] = values('Technique')
    longest = max((len(v) for v in lists.values()), default=0)
    return pd.DataFrame({name: pd.Series(v + [None] * (longest - len(v)), dtype=object) for name, v in lists.items()})


# ---------------------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------------------
def _nearest(term, vocabulary):
    import difflib
    match = difflib.get_close_matches(norm(term), [norm(v) for v in vocabulary], n=1, cutoff=0.82)
    if not match:
        return ''
    return next(v for v in vocabulary if norm(v) == match[0])


def check(tables):
    """Look the data over. Returns a dict of findings for the report; nothing here changes the data."""
    report = {'tables': {}, 'problems': [], 'worklists': {}}
    index = tables.get(INDEX_TABLE)
    lists = {c: [v for v in index[c].dropna()] for c in index.columns} if index is not None else {}

    for study, name in STUDY_TABLES.items():
        df = tables.get(name)
        if df is None:
            continue
        info = {'rows': len(df), 'columns': len(df.columns)}
        ids = df['ID'].dropna().astype(str)
        info['duplicate_ids'] = sorted(ids[ids.duplicated()].unique())[:20]
        info['blank_ids'] = int(df['ID'].isna().sum())
        info['single_combination'] = df['Single/Combination'].map(lambda v: v if v is not None else '(blank)').value_counts().to_dict() \
            if 'Single/Combination' in df.columns else {}
        if 'Male/Female' in df.columns:
            dates = df[df['Male/Female'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}')]
            info['sex_ratio_dates'] = len(dates)
            if len(dates):
                report['worklists'].setdefault('Sex ratio turned into a date', []).extend(
                    {'sheet': study, 'ID': r['ID'], 'value in sheet': r['Male/Female']} for _, r in dates.iterrows())
        for column, label in (('Drug_category', 'Drug category'), ('Cancer_Type', 'Cancer type')):
            if column in df.columns and lists.get(column):
                vocabulary = {norm(v) for v in lists[column]}
                bad = df[~df[column].map(norm).isin(vocabulary)]
                info[f'{column}_not_in_list'] = len(bad)
                for value, count in bad[column].fillna('(blank)').value_counts().items():
                    report['worklists'].setdefault(f'{label} not in the index list', []).append(
                        {'sheet': study, 'value in data': value, 'rows': int(count),
                         'closest list entry': _nearest(value, lists[column]) if value != '(blank)' else ''})
        report['tables'][study] = info

    technique_list = lists.get('Controlled_Technique', [])
    immune_list = lists.get('Controlled_Immune_Term', [])
    coverage = {}
    for kind, columns, vocabulary, label in (
            ('technique', [CONTROLLED_COLUMNS['technique']], technique_list, 'Technique term not in the controlled list'),
            ('immune', [CONTROLLED_COLUMNS[o] for o in IMMUNE_OUTCOMES], immune_list, 'Immune term not in the controlled list')):
        allowed = {norm(v) for v in vocabulary}
        uses = {}
        for study, name in STUDY_TABLES.items():
            df = tables.get(name)
            if df is None:
                continue
            for column in columns:
                if column in df.columns:
                    for value in df[column]:
                        for term in split_terms(value):
                            key = (norm(term), term)
                            uses[key] = uses.get(key, 0) + 1
        total = sum(uses.values())
        listed = sum(n for (k, _), n in uses.items() if k in allowed)
        coverage[kind] = {'mentions': total, 'in_list': listed, 'distinct_terms': len({k for k, _ in uses}),
                          'distinct_in_list': len({k for k, _ in uses if k in allowed}), 'list_size': len(vocabulary),
                          'list_never_used': sorted(v for v in vocabulary if norm(v) not in {k for k, _ in uses})}
        merged = {}
        for (k, term), n in uses.items():
            if k not in allowed:
                merged.setdefault(k, [term, 0])[1] += n
        report['worklists'][label] = [{'term in data': t, 'mentions': n, 'closest list entry': _nearest(t, vocabulary)}
                                      for t, n in sorted(merged.values(), key=lambda x: -x[1])]
        # list entries that differ only in spacing, case or punctuation
        compact = {}
        for v in vocabulary:
            compact.setdefault(re.sub(r'[^a-z0-9]', '', v.lower()), []).append(v)
        twins = [group for group in compact.values() if len(group) > 1]
        if twins:
            report['worklists'].setdefault('List entries that are near-duplicates', []).extend(
                {'list': kind, 'entries': ' | '.join(group)} for group in twins)
    report['coverage'] = coverage
    return report


def summarise(tables, notes, report):
    lines = []
    lines.append('Tables to write: ' + ', '.join(f"{name} ({len(df)} rows)" for name, df in tables.items()))
    for study, info in report['tables'].items():
        extra = []
        if info['duplicate_ids']:
            extra.append(f"DUPLICATE IDs: {info['duplicate_ids'][:5]}")
        if info['blank_ids']:
            extra.append(f"{info['blank_ids']} rows without an ID")
        for key in ('Drug_category_not_in_list', 'Cancer_Type_not_in_list'):
            if info.get(key):
                extra.append(f"{info[key]} rows with a {key.split('_not')[0].replace('_', ' ').lower()} that is not in the index list")
        if info.get('sex_ratio_dates'):
            extra.append(f"{info['sex_ratio_dates']} sex ratios stored as dates")
        lines.append(f"  {study}: {info['rows']} rows, {info['columns']} columns" + (' | ' + '; '.join(extra) if extra else ''))
    for kind, c in report.get('coverage', {}).items():
        if c['mentions']:
            lines.append(f"  controlled {kind} terms: {c['in_list'] / c['mentions']:.0%} of {c['mentions']} mentions are in the list "
                         f"({c['distinct_terms'] - c['distinct_in_list']} of {c['distinct_terms']} distinct terms are not)")
    for fixes_sheet, fixes in notes['id_fixes'].items():
        if fixes:
            lines.append(f"  removed the trailing '.0' from identifiers in '{fixes_sheet}': {fixes}")
    for dropped in notes['dropped_notes']:
        lines.append(f"  WARNING: column '{dropped['column']}' in '{dropped['sheet']}' has no heading and is left out, but holds text in "
                     f"{dropped['rows_with_text']} row(s), e.g. \"{dropped['example']}...\"")
    if notes['missing_sheets']:
        lines.append(f"  MISSING sheets: {notes['missing_sheets']}")
    return lines
