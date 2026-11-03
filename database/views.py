from django.shortcuts import render
from django.shortcuts import render,redirect,HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
import pandas as pd
from .all_search_count import *
import json 
import re
from .tools import *
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, DataStructs, MACCSkeys
from rdkit.Chem import rdMolAlign
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.exc import ProgrammingError



def load_data(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=column_names)
        df['mol'] = df['STR_LINK_(SMILES)'].apply(smiles_to_mol)
        df['valid_smiles'] = df['mol'].apply(lambda x: x is not None)
        return df
def index(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM "Master"')  # Adjust the query as needed
        rows = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]

    df = pd.DataFrame(rows, columns=column_names)
    json_records = df.reset_index().to_json(orient ='records')
    data = json.loads(json_records)
    context = {'d': data, 'column_names': column_names,'cell_line': 'cell_line_value',  # Replace with actual value
        'animal_studies': 'animal_studies_value',  # Replace with actual value
        'patient_studies': 'patient_studies_value',}
   
    
    return render(request,'database/index.html',context)

def get_columns(request):
    field = request.GET.get('field')
    column_names = []

    if field == 'patient_studies':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_Patient_Studies"')
            column_names = [col[0] for col in cursor.description]
    elif field == 'animal_studies':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_animal_studies"')
            column_names = [col[0] for col in cursor.description]
    elif field == 'cell_line':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_cell_line"')
            column_names = [col[0] for col in cursor.description]
    elif field=='all_fields':
        list1= []
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_cell_line"')
            for col in cursor.description:
                list1.append(col[0])
            cursor.execute('SELECT * FROM "Browse_by_Patient_Studies"')
            for col in cursor.description:
                list1.append(col[0])
            cursor.execute('SELECT * FROM "Browse_by_animal_studies"')            
            for col in cursor.description:
                list1.append(col[0])
        
    # convert the set to the list
        column_names = list1   

    return JsonResponse({'column_names': column_names})


from django.shortcuts import render
from django.db import connection

# def master_list(request):
#     with connection.cursor() as cursor:
#         cursor.execute('SELECT * FROM "Master"')  # Adjust the query as needed
#         rows = cursor.fetchall()
#         column_names = [col[0] for col in cursor.description]

#     df = pd.DataFrame(rows, columns=column_names)
#     json_records = df.reset_index().to_json(orient ='records')
#     data = json.loads(json_records)
#     context = {'d': data, 'column_names': column_names}

#     return render(request, 'database/masters.html', context)
def _browse_response(kind, outcome='any'):
    try:
        return JsonResponse(browse(kind, outcome))
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
        return JsonResponse({'error': 'Internal server error'}, status=500)


def drug_category(request):
    return _browse_response('drug_category')


def technique(request):
    return _browse_response('technique')


def cancer_type(request):
    return _browse_response('cancer_type')


def immune_terms(request):
    return _browse_response('immune', request.GET.get('outcome', 'any'))


def browse_term(request):
    """The studies behind one Browse count (kind: drug_category, cancer_type, technique or immune)."""
    try:
        results = studies_with(request.GET.get('kind', ''), request.GET.get('field', ''), request.GET.get('term', ''),
                               request.GET.get('outcome', 'any'))
    except (ValueError, KeyError) as e:
        return render(request, 'database/error.html', {'error_message': str(e)}, status=400)
    context = {'d': results.to_json(orient='records'), 'column_names': json.dumps(list(results.columns))}
    return render(request, 'database/masters.html', context)


def get_category_data(request, category):
    # Replace placeholder with `/`
    

    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM "Master"')
        rows = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=column_names)

    # Split the category into individual words for more flexible matching
    category_terms = category.split(',')

    # Create a mask to check if any of the category terms appear in any of the columns
    mask = df.apply(lambda row: any(term.lower() in row.astype(str).str.lower().to_string() for term in category_terms), axis=1)
    filtered_df = df[mask]

    json_records = filtered_df.reset_index().to_json(orient='records')
    data = json.loads(json_records)
    context = {'d': data, 'column_names': column_names}

    # Render the new template with the context
    return render(request, 'database/masters.html', context)

def search(request):
    if request.method == "POST":
        query = request.POST.get('query')
        selected_field = request.POST.get('field')
        specific_fields = request.POST.getlist('field_query')
        print("Query:", query)
        print("Selected Field:", selected_field)
        print("Specific Fields:", specific_fields)

        # Initialize an empty DataFrame to hold the final results
        final_df = pd.DataFrame()

        # Function to load data from a specified table and filter it based on the query
        def load_and_filter_data(table_name, fields):
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)

                # Filter DataFrame to find rows where selected fields contain the query
                if fields:
                    mask = df[fields].apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)
                    filtered_df = df[mask]
                    print(filtered_df)
                else:
                    filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
                    print(filtered_df)
                
                return filtered_df

        # Load and filter data based on the selected field
        if selected_field == 'all_fields':
            tables = ['Browse_by_Patient_Studies', 'Browse_by_animal_studies', 'Browse_by_cell_line']
            for table in tables:
                filtered_df = load_and_filter_data(table, specific_fields)
                final_df = pd.concat([final_df, filtered_df], ignore_index=True)
                
        else:
            table_mapping = {
                'patient_studies': 'Browse_by_Patient_Studies',
                'animal_studies': 'Browse_by_animal_studies',
                'cell_line': 'Browse_by_cell_line'
            }
            table_name = table_mapping.get(selected_field)
            if table_name:
                final_df = load_and_filter_data(table_name, specific_fields)

        context = {'d': final_df.to_json(orient='records'), 'column_names':json.dumps(final_df.columns.to_list())}

        # Render the results template with the context
        return render(request, 'database/masters.html', context)
    else:
        # If not a POST request, just render the search form
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Master"')
            rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]

        return render(request, 'database/index.html', {'column_names': column_names})


# def drug_search(request,pk):
#     print(pk)    
#     rows,column_names= search_drug(pk)      

#     df = pd.DataFrame(rows, columns=column_names)
#     json_records = df.reset_index().to_json(orient ='records')get_columnsget_columns
#     data = json.loads(json_records)
#     context = {'d': data, 'column_names': column_names,}
    
#     return render(request,'database/masters.html',context)
import json

def get_data(request, category, field, column):
    print("Category:", category)
    print("Field:", field)
    print("Column:", column)
    
    try:
        df, column_names = data_get(field)
        
        # Ensure column_names is a list of strings
        column_names = [str(col) for col in column_names]

        # Split the category by delimiters
        search_terms = re.split(r'[/,]', category)
        print("Search Terms:", search_terms)

        # Filter DataFrame to find rows where the specified field contains any of the search terms
        mask = df[column].apply(lambda x: any(term.strip().lower() in str(x).lower() for term in search_terms))
        filtered_df = df[mask]
        
        # Serialize the DataFrame and column names to JSON
        context = {
            'd': filtered_df.to_json(orient='records'),
            'column_names': json.dumps(column_names)
        }

        # Render the new template with the context
        return render(request, 'database/masters.html', context)
    
    except ValueError as e:
        return render(request, 'database/error.html', {'error_message': str(e)})
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'database/error.html', {'error_message': "An unexpected error occurred"})


def conditional_datasearch(request):
    
    return render(request,'database/msters.html')


# How a row's operator joins it to the next row ("not" means: and the next row must not match)
CONDITION_CONNECTORS = {'and': 'AND', 'or': 'OR', 'not': 'AND NOT'}


def conditional_search(request):
    if request.method == "POST":
        tables = request.POST.getlist('table[]')
        fields = request.POST.getlist('field[]')
        queries = request.POST.getlist('query[]')
        operators = request.POST.getlist('operator[]')

        if not tables or not (len(tables) == len(fields) == len(queries)):
            return JsonResponse({'error': 'Incomplete search conditions'}, status=400)

        # Determine the primary table from the first entry
        primary_table = TOOL_TABLES.get(tables[0], None)
        if not primary_table:
            return JsonResponse({'error': 'Invalid table selection'}, status=400)

        # Field names go into the SQL text, so only names that are real columns of the table are accepted
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{primary_table}" LIMIT 0')
            valid_columns = {col[0] for col in cursor.description}

        # Construct the WHERE clause; values are always passed as parameters
        where_clause = ""
        params = []
        previous_operator = None
        for i in range(len(tables)):
            if TOOL_TABLES.get(tables[i]) != primary_table:
                continue  # Only filtering on the primary table for simplicity

            if fields[i] not in valid_columns:
                return JsonResponse({'error': f"Unknown field '{fields[i]}'"}, status=400)

            # Join to the previous condition with that row's operator
            if where_clause:
                connector = CONDITION_CONNECTORS.get(previous_operator)
                if connector is None:
                    return JsonResponse({'error': 'Invalid operator'}, status=400)
                where_clause += f" {connector} "

            # Case-insensitive "contains" search
            where_clause += f"\"{fields[i]}\" ILIKE %s"
            params.append(f"%{queries[i]}%")
            previous_operator = operators[i].lower() if i < len(operators) else 'and'

        # Construct the final SQL query
        final_query = f"SELECT * FROM \"{primary_table}\" WHERE {where_clause}"

        # Print the final query and params for debugging
        print("Final SQL Query:", final_query)
        print("Query Parameters:", params)

        # Run the query
        with connection.cursor() as cursor:
            cursor.execute(final_query, params)  # Pass the params list to execute to avoid SQL injection
            rows = cursor.fetchall()

            # Fetch the column names
            column_names = [col[0] for col in cursor.description]

            # Convert the results into a list of dictionaries
            result_data = []
            for row in rows:
                result_data.append(dict(zip(column_names, row)))

        # Return results as JSON (or in a template if needed)
        context = {
            'd': json.dumps(result_data),
            'column_names': json.dumps(column_names)
        }

        return render(request, 'database/masters.html', context)

    else:
        # Handle the GET request (initial load)
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Master"')  # Adjust table name as needed
            rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]

        return render(request, 'database/index.html', {'column_names': column_names})

    
def smiles_search(request):
    if request.method == "POST":
        field = request.POST.get('field')
        smiles = request.POST.get('smiles')
        pubchemid = request.POST.get('pubchemid')
        drugbankid = request.POST.get('drugbankid')

        columns_to_search = {
            'smiles': 'STR_LINK_(SMILES)',
            'pubchemid': 'DRUG_PUBCHEM',
            'drugbankid': 'Drugbank_ID'
        }
        queries = {
            'smiles': smiles,
            'pubchemid': pubchemid,
            'drugbankid': drugbankid
        }

        def escape_special_chars(query):
            return re.escape(query)

        def load_and_filter_data(table_name, columns_to_search, queries):
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)

                masks = []
                for key, column in columns_to_search.items():
                    query = queries[key]
                    if query:
                        escaped_query = escape_special_chars(query)
                        mask = df[column].astype(str).str.contains(escaped_query, case=False, na=False)
                        masks.append(mask)
                
                if masks:
                    combined_mask = masks[0]
                    for mask in masks[1:]:
                        combined_mask |= mask
                    filtered_df = df[combined_mask]
                else:
                    filtered_df = pd.DataFrame(columns=column_names)

                return filtered_df

        table_mapping = {
            'patient_studies': 'Browse_by_Patient_Studies',
            'animal_studies': 'Browse_by_animal_studies',
            'cell_line': 'Browse_by_cell_line'
        }
        table_name = table_mapping.get(field, 'Browse_by_patient_studies')

        filtered_df = load_and_filter_data(table_name, columns_to_search, queries)

        context = {
            'd': filtered_df.to_json(orient='records'),
            'column_names': json.dumps(filtered_df.columns.tolist())
        }

        return render(request, 'database/masters.html', context)
    else:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Master"')
            rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]

        return render(request, 'database/index.html', {'column_names': column_names})
    
    
    
#*******************************************************Tools Funtion Start**************************************************************************************
TOOL_TABLES = {
    'patient_studies': 'Browse_by_Patient_Studies',
    'animal_studies': 'Browse_by_animal_studies',
    'cell_line': 'Browse_by_cell_line',
}
TOOL_RESULT_COLUMNS = [
    'ID', 'STR_LINK_(SMILES)', None,  # None is replaced by each tool's score column
    'Immune_System_function_unaffected',
    'Immune_System-Function_enhanced/numbers_increased',
    'Immune_System-Function_inhibited/numbers_decreased',
    'Negative_Immune_System_regulation_-Function_enhanced/numbers_in',
]
DEFAULT_THRESHOLD = 0.5      # 2D (Morgan) and MACCS fingerprint searches
DEFAULT_THRESHOLD_3D = 0.5   # unrelated structures score ~0.35-0.4 in 3D, so 0.4 would return a quarter to a half of the database


def _tool_error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _parse_threshold(raw, default):
    """Parse a 0-1 similarity cut-off. Returns (value, error message); blank means default."""
    if raw is None or str(raw).strip() == '':
        return default, None
    try:
        value = float(raw)
    except ValueError:
        return None, 'Threshold must be a number between 0 and 1.'
    if not 0 <= value <= 1:
        return None, 'Threshold must be between 0 and 1.'
    return value, None


def _tool_dataframe(field):
    """Study table for the tools, with parsed molecules; None for an unknown study type."""
    table = TOOL_TABLES.get(field)
    return load_data(table) if table else None


def _tool_results(hits, score_column):
    """Result rows for the tool tables; missing values become null, not NaN (invalid JSON)."""
    columns = [score_column if c is None else c for c in TOOL_RESULT_COLUMNS]
    rows = hits[columns].astype(object)
    return rows.where(rows.notna(), None).to_dict(orient='records')


def _tool_info(method, total, searched, matches, threshold=None):
    """Summary shown above the results: what was searched and how many entries had no usable structure."""
    info = {'method': method, 'software': f'RDKit {rdBase.rdkitVersion}', 'entries_total': int(total),
            'entries_searched': int(searched), 'matches': int(matches)}
    if threshold is not None:
        info['threshold'] = threshold
    return info


# The search functions below are shared by the web views and by the API (database/api.py).
# Each takes the study table (with parsed molecules), the query molecule and a threshold, and returns
# (hits, name of the score column, summary); entries without a usable structure never match.
def _per_structure(df, score):
    """score(mol) for every row, computed once per distinct structure: the same drug appears in many studies."""
    distinct = df.drop_duplicates('STR_LINK_(SMILES)')
    scores = {smiles: score(mol) for smiles, mol in zip(distinct['STR_LINK_(SMILES)'], distinct['mol'])}
    return df['STR_LINK_(SMILES)'].map(scores)


def _search_2d(df, query_mol, threshold):
    df['2d_similarity'] = _per_structure(df, lambda mol: calculate_2d_similarity(query_mol, mol))
    df['2d_similarity'] = df.apply(lambda row: row['2d_similarity'] if row['valid_smiles'] else -1, axis=1)
    hits = df[df['2d_similarity'] >= threshold].sort_values(by='2d_similarity', ascending=False)
    info = _tool_info(f'Morgan fingerprint (radius {MORGAN_RADIUS}, {MORGAN_NBITS} bits), Tanimoto coefficient',
                      len(df), df['valid_smiles'].sum(), len(hits), threshold)
    return hits, '2d_similarity', info


def _search_3d(df, query_mol, threshold):
    # Align the query's conformers onto each stored 3D model and score the shape overlap (raises ValueError for unusable queries)
    scores, _, _ = similarity_3d_scores(query_mol, df['STR_LINK_(SMILES)'])
    df['3d_similarity'] = df['STR_LINK_(SMILES)'].map(scores)  # NaN where there is no 3D model
    hits = df[df['3d_similarity'] >= threshold].sort_values(by='3d_similarity', ascending=False)
    info = _tool_info(f'Shape Tanimoto after Crippen-O3A alignment (RDKit); best of up to {QUERY_CONFORMERS} query conformers',
                      len(df), df['3d_similarity'].notna().sum(), len(hits), threshold)
    return hits, '3d_similarity', info


def _search_substructure(df, query_mol, threshold=None):
    # Keep database molecules that contain the query
    df['substructure_match'] = df['mol'].apply(lambda mol: is_substructure(query_mol, mol))
    hits = df[df['substructure_match'] == True]
    info = _tool_info('Exact substructure match (RDKit HasSubstructMatch)',
                      len(df), df['valid_smiles'].sum(), len(hits))
    return hits, 'substructure_match', info


def _search_maccs(df, query_mol, threshold):
    df['maccs_similarity'] = _per_structure(df, lambda mol: calculate_maccs_similarity(query_mol, mol) if mol is not None else -1).fillna(-1)
    hits = df[df['maccs_similarity'] >= threshold].sort_values(by='maccs_similarity', ascending=False)
    info = _tool_info('MACCS keys (166 bits), Tanimoto coefficient',
                      len(df), df['valid_smiles'].sum(), len(hits), threshold)
    return hits, 'maccs_similarity', info


# method -> (search function, default threshold or None when the method has no threshold)
SIMILARITY_METHODS = {
    '2d': (_search_2d, DEFAULT_THRESHOLD),
    '3d': (_search_3d, DEFAULT_THRESHOLD_3D),
    'maccs': (_search_maccs, DEFAULT_THRESHOLD),
    'substructure': (_search_substructure, None),
}


def _run_tool(request, method):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    query_smiles = request.POST.get('smiles')
    field = request.POST.get('field')
    if not query_smiles or not field:
        return _tool_error('Please enter a SMILES string and select a study type.')

    search, default_threshold = SIMILARITY_METHODS[method]
    threshold = None
    if default_threshold is not None:
        threshold, error = _parse_threshold(request.POST.get('threshold'), default_threshold)
        if error:
            return _tool_error(error)

    query_mol = smiles_to_mol(query_smiles)
    if query_mol is None:
        return _tool_error('Invalid SMILES')

    df = _tool_dataframe(field)
    if df is None:
        return _tool_error('Invalid field selection')

    try:
        hits, score_column, info = search(df, query_mol, threshold)
    except ValueError as e:
        return _tool_error(str(e))

    results = _tool_results(hits, score_column)
    response = {'success': True, 'results': results, 'info': info}
    if method == '3d':
        response['columns'] = list(results[0].keys()) if results else []
    return JsonResponse(response)


# View for Tanimoto 2D similarity search
def tanimoto_search(request):
    return _run_tool(request, '2d')


# View for 3D shape similarity search
def third_search(request):
    return _run_tool(request, '3d')


# View for substructure search
def substructure_search(request):
    return _run_tool(request, 'substructure')


# View for MACCS key-based similarity search
def maccs_search(request):
    return _run_tool(request, 'maccs')



def get_columns1(request):
    field = request.GET.get('field')
    if not field:
        return JsonResponse({'success': False, 'error': 'No field provided'})
 
    if field == 'patient_studies':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_Patient_Studies"')
            column_names = [col[0] for col in cursor.description]
        
    elif field == 'animal_studies':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_animal_studies"')
            column_names = [col[0] for col in cursor.description]
        
    elif field == 'cell_line':
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Browse_by_cell_line"')
            column_names = [col[0] for col in cursor.description]
        
    else:
        return JsonResponse({'success': False, 'error': 'Invalid field selection'})

    return JsonResponse({'success': True, 'columns': column_names})


import re
import json
import pandas as pd
from django.http import JsonResponse
import traceback

def sanitize_column_name(name):
    """Sanitize column names by replacing invalid characters with underscores."""
    return re.sub(r'\W+', '_', name).lower()

def submit_data(request):
    # Define the file path for your Excel file
    excel_file = "local_database.xlsx"

    if request.method == 'POST':
        try:
            # Parse JSON request body
            data = json.loads(request.body.decode('utf-8'))
            print("Data received:", data)

            # Extract selected database
            selected_database = data.pop('selected_database', None)
            if not selected_database:
                return JsonResponse({'success': False, 'error': 'Missing selected_database field'})

            # Map selected database to sheet names in the Excel file
            sheet_mapping = {
                'cell_line': 'database_cellstudy',
                'animal_studies': 'database_animalstudy',
                'patient_studies': 'database_patientstudy'
            }
            sheet_name = sheet_mapping.get(selected_database)
            if not sheet_name:
                return JsonResponse({'success': False, 'error': 'Invalid database selected'})

            # Sanitize the keys in the JSON data
            sanitized_data = {sanitize_column_name(key): value for key, value in data.items()}

            # Load or create the Excel file
            try:
                # Try to load existing Excel file
                with pd.ExcelWriter(excel_file, mode="a", if_sheet_exists="overlay", engine="openpyxl") as writer:
                    # Check if the sheet already exists
                    try:
                        existing_data = pd.read_excel(excel_file, sheet_name=sheet_name)
                    except ValueError:
                        existing_data = pd.DataFrame()  # If sheet doesn't exist, create an empty DataFrame

                    # Convert new data to a DataFrame
                    new_data = pd.DataFrame([sanitized_data])

                    # Combine existing data with new data
                    combined_data = pd.concat([existing_data, new_data], ignore_index=True)

                    # Write the updated data to the appropriate sheet
                    combined_data.to_excel(writer, sheet_name=sheet_name, index=False)

            except FileNotFoundError:
                # Create a new Excel file if it doesn't exist
                with pd.ExcelWriter(excel_file, mode="w", engine="openpyxl") as writer:
                    new_data = pd.DataFrame([sanitized_data])
                    new_data.to_excel(writer, sheet_name=sheet_name, index=False)

            return JsonResponse({'success': True})

        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            print("Unexpected Error:", traceback.format_exc())
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

