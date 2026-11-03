"""Read-only public API: filtered browsing, full-dataset download and the structure searches.

Everything is GET-only and returns JSON (or CSV where asked), so it works from curl, wget, R or Python.
The tables are read as they are stored, with every column, and cached briefly to spare the database.
"""
import json
import logging
from functools import wraps

import pandas as pd
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse

from . import tools
from .views import SIMILARITY_METHODS, TOOL_TABLES, _parse_threshold, load_data

logger = logging.getLogger(__name__)

API_VERSION = '1'
CACHE_SECONDS = getattr(settings, 'API_CACHE_SECONDS', 60)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
STUDY_TYPES = ('cell_line', 'animal_studies', 'patient_studies')
RESERVED_PARAMS = {'limit', 'offset', 'format', 'q', 'exact'}


class ApiError(Exception):
    def __init__(self, message, status=400, **extra):
        super().__init__(message)
        self.status = status
        self.extra = extra


def api_view(view):
    """GET/HEAD only; errors become JSON; every response is readable from any origin."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.method not in ('GET', 'HEAD'):
            response = JsonResponse({'error': 'Only GET is supported.'}, status=405)
            response['Allow'] = 'GET, HEAD'
        else:
            try:
                response = view(request, *args, **kwargs)
            except ApiError as e:
                response = JsonResponse({'error': str(e), **e.extra}, status=e.status)
            except Exception:
                logger.exception('API request failed: %s', request.get_full_path())
                response = JsonResponse({'error': 'Internal server error.'}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        response['X-API-Version'] = API_VERSION
        return response
    return wrapper


def _study_frame(study_type):
    table = TOOL_TABLES.get(study_type)
    if table is None:
        raise ApiError(f"Unknown study type '{study_type}'.", 404, valid_values=list(STUDY_TYPES))
    key = f'api:study:{study_type}'
    df = cache.get(key)
    if df is None:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{table}"')
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        cache.set(key, df, CACHE_SECONDS)
    return df


def _records(df):
    # to_json turns missing values into null (plain to_dict would leave NaN, which is not valid JSON)
    return json.loads(df.to_json(orient='records', force_ascii=False))


def _int_param(request, name, default, minimum, maximum):
    raw = request.GET.get(name)
    if raw in (None, ''):
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(f"'{name}' must be a whole number.")
    if not minimum <= value <= maximum:
        raise ApiError(f"'{name}' must be between {minimum} and {maximum}.")
    return value


def _format_param(request):
    fmt = request.GET.get('format', 'json').lower()
    if fmt not in ('json', 'csv'):
        raise ApiError("'format' must be 'json' or 'csv'.")
    return fmt


def _filter(df, request):
    """Field filters (?Drug=gemcitabine) match case-insensitively as substrings, or exactly with exact=true; q searches every field.
    Field names are not case-sensitive either."""
    exact = request.GET.get('exact', '').lower() in ('1', 'true', 'yes')
    by_name = {str(c).lower(): c for c in df.columns}
    for name in request.GET:
        if name.lower() in RESERVED_PARAMS:
            continue
        column = by_name.get(name.lower())
        if column is None:
            raise ApiError(f"Unknown field '{name}'.", 400, valid_fields=list(df.columns))
        text = df[column].fillna('').astype(str)
        for value in request.GET.getlist(name):
            mask = text.str.lower() == value.lower() if exact else text.str.contains(value, case=False, regex=False)
            df, text = df[mask], text[mask]
    q = request.GET.get('q', '')
    if q:
        mask = pd.Series(False, index=df.index)
        for column in df.columns:
            mask |= df[column].fillna('').astype(str).str.contains(q, case=False, regex=False)
        df = df[mask]
    return df


def _csv_response(df, filename, attachment=True):
    response = HttpResponse(df.to_csv(index=False), content_type='text/csv; charset=utf-8')
    if attachment:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view
def index(request):
    base = request.build_absolute_uri('/api/v1/')
    return JsonResponse({
        'name': 'CancerImmunoDB API',
        'version': API_VERSION,
        'study_types': list(STUDY_TYPES),
        'endpoints': {
            'status': base + 'status/',
            'fields': base + 'fields/',
            'studies': base + 'studies/{study_type}/?limit=100&offset=0&format=json|csv&q=text&{field}=value&exact=true',
            'download': base + 'download/{cell_line|animal_studies|patient_studies|all}.{csv|json}',
            'similarity': base + 'similarity/?smiles=...&method=2d|maccs|substructure|3d&study_type=cell_line&threshold=0.5',
        },
        'documentation': request.build_absolute_uri('/#api'),
    })


@api_view
def status(request):
    """Row counts straight from the database (not cached), so it doubles as a health check for uptime monitors."""
    try:
        counts = {}
        with connection.cursor() as cursor:
            for study_type in STUDY_TYPES:
                cursor.execute(f'SELECT COUNT(*) FROM "{TOOL_TABLES[study_type]}"')
                counts[study_type] = cursor.fetchone()[0]
    except Exception:
        logger.exception('API status check failed')
        return JsonResponse({'status': 'error', 'api_version': API_VERSION}, status=503)
    return JsonResponse({'status': 'ok', 'api_version': API_VERSION, 'studies': counts, 'total': sum(counts.values())})


@api_view
def fields(request):
    return JsonResponse({study_type: list(_study_frame(study_type).columns) for study_type in STUDY_TYPES})


@api_view
def study_list(request, study_type):
    fmt = _format_param(request)
    limit = _int_param(request, 'limit', DEFAULT_LIMIT, 1, MAX_LIMIT)
    offset = _int_param(request, 'offset', 0, 0, 10 ** 9)

    df = _filter(_study_frame(study_type), request)
    total = len(df)
    page = df.iloc[offset:offset + limit]
    if fmt == 'csv':
        return _csv_response(page, f'cancerimmunodb_{study_type}.csv', attachment=False)

    next_url = None
    if offset + limit < total:
        params = request.GET.copy()
        params['offset'] = offset + limit
        next_url = f'{request.build_absolute_uri(request.path)}?{params.urlencode()}'
    return JsonResponse({'study_type': study_type, 'total': total, 'count': len(page), 'limit': limit,
                         'offset': offset, 'next': next_url, 'results': _records(page)},
                        json_dumps_params={'ensure_ascii': False})


@api_view
def download(request, study, fmt):
    """The whole table in one file. 'all' stacks the three tables and adds a study_type column."""
    if study == 'all':
        frames = []
        for study_type in STUDY_TYPES:
            frame = _study_frame(study_type).copy()
            frame.insert(0, 'study_type', study_type)
            frames.append(frame)
        df = pd.concat(frames, ignore_index=True, sort=False)
    else:
        df = _study_frame(study)

    filename = f'cancerimmunodb_{study}.{fmt}'
    if fmt == 'csv':
        response = _csv_response(df, filename)
    else:
        response = HttpResponse(json.dumps(_records(df), ensure_ascii=False), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Cache-Control'] = f'public, max-age={CACHE_SECONDS}'
    return response


@api_view
def similarity(request):
    """The four structure searches over GET. Returns full records plus the score and a summary of what was searched."""
    smiles = request.GET.get('smiles', '').strip()
    if not smiles:
        raise ApiError("'smiles' is required.")
    method = request.GET.get('method', '2d').lower()
    if method not in SIMILARITY_METHODS:
        raise ApiError(f"Unknown method '{method}'.", 400, valid_values=list(SIMILARITY_METHODS))
    study_type = request.GET.get('study_type', 'cell_line')
    if study_type not in STUDY_TYPES:
        raise ApiError(f"Unknown study type '{study_type}'.", 400, valid_values=list(STUDY_TYPES))
    limit = _int_param(request, 'limit', DEFAULT_LIMIT, 1, MAX_LIMIT)

    search, default_threshold = SIMILARITY_METHODS[method]
    threshold = None
    if default_threshold is not None:
        threshold, error = _parse_threshold(request.GET.get('threshold'), default_threshold)
        if error:
            raise ApiError(error)

    query_mol = tools.smiles_to_mol(smiles)
    if query_mol is None:
        raise ApiError('Invalid SMILES.')

    try:
        hits, score_column, info = search(load_data(TOOL_TABLES[study_type]), query_mol, threshold)
    except ValueError as e:
        raise ApiError(str(e))

    hits = hits.drop(columns=['mol', 'valid_smiles'], errors='ignore')
    return JsonResponse({'study_type': study_type, 'method': method, 'score_field': score_column, 'info': info,
                         'count': min(len(hits), limit), 'results': _records(hits.head(limit))},
                        json_dumps_params={'ensure_ascii': False})
