"""Check whether drugs or articles, for example ones suggested by a literature search, are already in the database."""

STUDY_TYPES = ('cell_line', 'animal_studies', 'patient_studies')


def _pmid_key(value):
    text = str(value).strip()
    return text[:-2] if text.endswith('.0') else text  # some tables store PMIDs as "21052994.0"


def _column(df, name):
    """The column called `name`, whatever its capitalisation (the tables say "Drug", older copies "DRUG")."""
    for column in df.columns:
        if str(column).lower() == name.lower():
            return column
    raise KeyError(f"no '{name}' column")


def _row(kind, query, counts):
    empty = [study for study in STUDY_TYPES if counts[study] == 0]
    if not empty:
        status = 'in all study types'
    elif len(empty) == len(STUDY_TYPES):
        status = 'not in the database'
    else:
        status = 'no entries in: ' + ', '.join(empty)
    return {'kind': kind, 'query': query, **counts, 'status': status}


def check_candidates(frames, drugs=(), pmids=()):
    """frames maps each study type to its table. A drug matches when its name appears in the DRUG field, so
    combination entries ("Gemcitabine + cisplatin") count too; a PMID must match exactly."""
    rows = []
    for drug in drugs:
        needle = drug.strip()
        counts = {study: int(frames[study][_column(frames[study], 'drug')].fillna('').astype(str)
                             .str.contains(needle, case=False, regex=False).sum()) for study in STUDY_TYPES}
        rows.append(_row('drug', needle, counts))
    for pmid in pmids:
        key = _pmid_key(pmid)
        counts = {study: int((frames[study][_column(frames[study], 'pmid')].dropna().map(_pmid_key) == key).sum())
                  for study in STUDY_TYPES}
        rows.append(_row('pmid', key, counts))
    return rows
