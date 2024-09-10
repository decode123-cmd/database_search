from django.shortcuts import render
from django.shortcuts import render,redirect,HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
import pandas as pd
from .all_search_count import *
import json 
import re
from .tools import *
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs, MACCSkeys
from rdkit.Chem import rdMolAlign


# Function to load data from a specified table
# Function to load data from a specified table

def load_data(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=column_names)
        df['mol'] = df['STR_LINK (SMILES)'].apply(smiles_to_mol)
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
def drug_category(request):
    try:
        response_data = {}
        counts = category()
        response_data['table'] = counts
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
        return JsonResponse({'error': 'Internal server error'}, status=500)
    
def technique(request):
    
    try:
        response_data = {}
        counts = techniques()
        response_data['table'] = counts
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
        return JsonResponse({'error': 'Internal server error'}, status=500)

def cancer_type(request):    
    try:
        response_data = {}
        counts = cancer()
        response_data['table'] = counts
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
        return JsonResponse({'error': 'Internal server error'}, status=500)
    

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


def conditional_search(request):
    if request.method == "POST":
        tables = request.POST.getlist('table[]')
        fields = request.POST.getlist('field[]')
        queries = request.POST.getlist('query[]')
        operators = request.POST.getlist('operator[]')

        final_df = pd.DataFrame()

        def load_and_filter_data(table_name, field, query, operator=None):
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)

                if operator == 'NOT':
                    mask = ~df[field].astype(str).str.contains(query, case=False, na=False)
                else:
                    mask = df[field].astype(str).str.contains(query, case=False, na=False)

                filtered_df = df[mask]
                return filtered_df

        for i in range(len(tables)):
            table_mapping = {
                'patient_studies': 'Browse_by_patient_studies',
                'animal_studies': 'Browse_by_animal_studies',
                'cell_line': 'Browse_by_cell_line'
            }
            table_name = table_mapping.get(tables[i])
            if table_name:
                filtered_df = load_and_filter_data(table_name, fields[i], queries[i], operators[i])
                if final_df.empty:
                    final_df = filtered_df
                else:
                    if operators[i-1] == 'AND':
                        final_df = final_df.merge(filtered_df, how='inner')
                    elif operators[i-1] == 'OR':
                        final_df = pd.concat([final_df, filtered_df]).drop_duplicates().reset_index(drop=True)
                    elif operators[i-1] == 'NOT':
                        final_df = final_df[~final_df.isin(filtered_df).all(axis=1)]

        columns_names = json.dumps(final_df.columns.tolist())
        d = final_df.to_json(orient='records')

        context = {'d': d, 'column_names': columns_names}

        return render(request, 'database/masters.html', context)
    else:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Master"')
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
            'smiles': 'STR_LINK (SMILES)',
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
# View for Tanimoto 2D similarity search
def tanimoto_search(request):
    if request.method == "POST":
        query_smiles = request.POST.get('smiles')
        field = request.POST.get('field')
        threshold = request.POST.get('threshold')
        
        if not query_smiles or not field or not threshold:
            return JsonResponse({'error': 'Invalid SMILES, field, or threshold'}, status=400)
        
        try:
            threshold = float(threshold)
        except ValueError:
            return JsonResponse({'error': 'Invalid threshold value'}, status=400)

        query_mol = smiles_to_mol(query_smiles)
        if query_mol is None:
            return JsonResponse({'error': 'Invalid SMILES'}, status=400)

        # Load data based on the selected field
        if field == 'patient_studies':
            df = load_data('Browse_by_Patient_Studies')
            print(df)
        elif field == 'animal_studies':
            df = load_data('Browse_by_animal_studies')
        elif field == 'cell_line':
            df = load_data('Browse_by_cell_line')
        else:
            return JsonResponse({'error': 'Invalid field selection'}, status=400)
        
        print("Data Loaded:", df.shape)

        # Perform 2D similarity search
        df['2d_similarity'] = df['mol'].apply(lambda mol: calculate_2d_similarity(query_mol, mol))
        
        # Handle invalid SMILES by setting a very low similarity score
        df['2d_similarity'] = df.apply(lambda row: row['2d_similarity'] if row['valid_smiles'] else -1, axis=1)
        
        # Filter and sort results
        results_2d = df[df['2d_similarity'] >= threshold]
        
        print("Filtered Results:", results_2d.shape)

        # Create a results dictionary
        results_dict = results_2d[['ID','STR_LINK (SMILES)', '2d_similarity','IMMUNE SYTEM FUNCTION UNAFFECTED','IMMUNE SYSTEM-Function enhanced/numbers increased','IMMUNE SYSTEM-Function inhibited/numbers decreased','NEGATIVE IMMUNE SYTEM REGULATION']].to_dict(orient='records')
        return JsonResponse({'success': True, 'results': results_dict}, safe=False)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def third_search(request):
    if request.method == "POST":
        query_smiles = request.POST.get('smiles', None)
        field = request.POST.get('field', None)
        threshold = request.POST.get('threshold', 0.5)
        
        if not query_smiles or not field:
            return JsonResponse({'error': 'Invalid SMILES or field'}, status=400)
        
        try:
            threshold = float(threshold)
        except ValueError:
            return JsonResponse({'error': 'Invalid threshold value'}, status=400)

        query_mol = smiles_to_mol(query_smiles)
        if query_mol is None:
            return JsonResponse({'error': 'Invalid SMILES'}, status=400)

        # Load data based on the selected field
        if field == 'patient_studies':
            df = load_data('Browse_by_Patient_Studies')
        elif field == 'animal_studies':
            df = load_data('Browse_by_animal_studies')
        elif field == 'cell_line':
            df = load_data('Browse_by_cell_line')
        else:
            return JsonResponse({'error': 'Invalid field selection'}, status=400)

        # Perform 3D similarity search
        df['3d_similarity'] = df['mol'].apply(lambda mol: calculate_3d_similarity(query_mol, mol) if mol is not None else -1)
        
        # Filter and sort results
        results_3d = df[df['3d_similarity'] >= threshold].sort_values(by='3d_similarity', ascending=False)
        print(results_3d)
        # Create a results dictionary
        results_dict = results_3d[['ID','STR_LINK (SMILES)', '3d_similarity','IMMUNE SYTEM FUNCTION UNAFFECTED','IMMUNE SYSTEM-Function enhanced/numbers increased','IMMUNE SYSTEM-Function inhibited/numbers decreased','NEGATIVE IMMUNE SYTEM REGULATION']].to_dict(orient='records')
        
        return JsonResponse({'success': True, 'results': results_dict}, safe=False)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
# View for substructure search
def substructure_search(request):
    if request.method == "POST":
        query_smiles = request.POST.get('smiles', None)
        field = request.POST.get('field', None)
        
        if not query_smiles or not field:
            return JsonResponse({'error': 'Invalid SMILES or field'}, status=400)

        query_mol = smiles_to_mol(query_smiles)
        if query_mol is None:
            return JsonResponse({'error': 'Invalid SMILES'}, status=400)

        # Load data based on the selected field
        if field == 'patient_studies':
            df = load_data('Browse_by_Patient_Studies')
        elif field == 'animal_studies':
            df = load_data('Browse_by_animal_studies')
        elif field == 'cell_line':
            df = load_data('Browse_by_cell_line')
        else:
            return JsonResponse({'error': 'Invalid field selection'}, status=400)

        # Perform substructure search
        df['substructure_match'] = df['mol'].apply(lambda mol: is_substructure(query_mol, mol))
        
        # Filter results
        results_substructure = df[df['substructure_match'] == True]
        
        # Create a results dictionary
        results_dict = results_substructure[['ID','STR_LINK (SMILES)', 'substructure_match','IMMUNE SYTEM FUNCTION UNAFFECTED','IMMUNE SYSTEM-Function enhanced/numbers increased','IMMUNE SYSTEM-Function inhibited/numbers decreased','NEGATIVE IMMUNE SYTEM REGULATION']].to_dict(orient='records')
        
        return JsonResponse({'success': True, 'results': results_dict}, safe=False)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# View for MACCS key-based similarity search
def maccs_search(request):
    if request.method == "POST":
        query_smiles = request.POST.get('smiles', None)
        field = request.POST.get('field', None)
        threshold = request.POST.get('threshold', 0.5)
        
        if not query_smiles or not field:
            return JsonResponse({'error': 'Invalid SMILES or field'}, status=400)
        
        try:
            threshold = float(threshold)
        except ValueError:
            return JsonResponse({'error': 'Invalid threshold value'}, status=400)

        query_mol = smiles_to_mol(query_smiles)
        if query_mol is None:
            return JsonResponse({'error': 'Invalid SMILES'}, status=400)

        # Load data based on the selected field
        if field == 'patient_studies':
            df = load_data('Browse_by_Patient_Studies')
        elif field == 'animal_studies':
            df = load_data('Browse_by_animal_studies')
        elif field == 'cell_line':
            df = load_data('Browse_by_cell_line')
        else:
            return JsonResponse({'error': 'Invalid field selection'}, status=400)

        # Perform MACCS key-based similarity search
        df['maccs_similarity'] = df['mol'].apply(lambda mol: calculate_maccs_similarity(query_mol, mol) if mol is not None else -1)
        
        # Filter and sort results
        results_maccs = df[df['maccs_similarity'] >= threshold].sort_values(by='maccs_similarity', ascending=False)
               
        # Create a results dictionary
        results_dict = results_maccs[['ID','STR_LINK (SMILES)', 'maccs_similarity','IMMUNE SYTEM FUNCTION UNAFFECTED','IMMUNE SYSTEM-Function enhanced/numbers increased','IMMUNE SYSTEM-Function inhibited/numbers decreased','NEGATIVE IMMUNE SYTEM REGULATION']].to_dict(orient='records')
        
        return JsonResponse({'success': True, 'results': results_dict}, safe=False)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



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
