from django.shortcuts import render
from django.shortcuts import render,redirect,HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
import pandas as pd
import psycopg2
from psycopg2 import sql
# Database connection parameters
db_params = {
    'dbname': 'railway',       # Use 'search' as default
    'user':  'postgres',
    'password': 'EiwSTHPfQiMNJHeSEAbsGRLpTIiDvEvT',
    'host':'cancerimmuno-production.up.railway.app',
    'port': 5432,
}
connection = psycopg2.connect(**db_params)

def category():
    try:
        response_data = {}
        with connection.cursor() as cursor:
            queries = {
                'index': 'SELECT * FROM "Browse_by_index1"',
                'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
                'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
                'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
            }
            dataframes = {}
            for key, query in queries.items():
                cursor.execute(query)
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                dataframes[key] = pd.DataFrame([dict(zip(column_names, row)) for row in rows])

            drug_categories = dataframes['index']['Drug category'].unique()
            counts = {
                category: {
                    'Cell_Count': len(dataframes['cell_line'][dataframes['cell_line']['Drug category'] == category]),
                    'Animal_Count': len(dataframes['animal_studies'][dataframes['animal_studies']['Drug category'] == category]),
                    'Patient_Count': len(dataframes['patients'][dataframes['patients']['Drug category'] == category])
                } for category in drug_categories
            }
            
    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
    
    return counts


def techniques():
    try:
        response_data = {}
        with connection.cursor() as cursor:
            queries = {
                'index': 'SELECT * FROM "Browse_by_index"',
                'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
                'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
                'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
            }
            dataframes = {}
            for key, query in queries.items():
                cursor.execute(query)
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                dataframes[key] = pd.DataFrame([dict(zip(column_names, row)) for row in rows])

            drug_categories = dataframes['index']['TECHNIQUE'].dropna().unique()  # Drop None values before finding unique
            search_terms = {}

            for category in drug_categories:
                terms = [term.strip() for term in category.split('/')]
                search_terms[category] = terms

            counts = {}

            for category, terms in search_terms.items():
                counts[category] = {
                    'Cell_Count': int(dataframes['cell_line']['TECHNIQUE'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum()),
                    'Animal_Count': int(dataframes['animal_studies']['TECHNIQUE'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum()),
                    'Patient_Count': int(dataframes['patients']['TECHNIQUE'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum())
                }

            return counts

    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
        return {}

def cancer():
    try:
        response_data = {}
        with connection.cursor() as cursor:
            queries = {
                'index': 'SELECT * FROM "Browse_by_index"',
                'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
                'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
                'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
            }
            dataframes = {}
            for key, query in queries.items():
                cursor.execute(query)
                rows = cursor.fetchall()
                column_names = [col[0] for col in cursor.description]
                dataframes[key] = pd.DataFrame([dict(zip(column_names, row)) for row in rows])

            drug_categories = dataframes['index']['Cancer_Type'].unique()
            counts = {
                category: {
                    'Cell_Count': len(dataframes['cell_line'][dataframes['cell_line']['Cancer_Type'] == category]),
                    'Animal_Count': len(dataframes['animal_studies'][dataframes['animal_studies']['Cancer_Type'] == category]),
                    'Patient_Count': len(dataframes['patients'][dataframes['patients']['Cancer_Type'] == category])
                } for category in drug_categories
            }
            
    except Exception as e:
        print(f"Error processing request: {e}")  # This will log to your server logs
    
    return counts


# def search_drug(pk):
#     if pk=='cell_line_value':        
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT * FROM "Browse_by_cell_line"')  # Adjust the query as needed
#             rows = cursor.fetchall()
#             column_names = [col[0] for col in cursor.description]
            
#     elif pk=='animal_studies_value':
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT * FROM "Browse_by_animal_studies"')  # Adjust the query as needed
#             rows = cursor.fetchall()
#             column_names = [col[0] for col in cursor.description]
            
#     elif pk=='patient_studies_value':
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT * FROM "Browse_by_Patient_Studies"')  # Adjust the query as needed
#             rows = cursor.fetchall()
#             column_names = [col[0] for col in cursor.description]
#     return rows,column_names
    



def data_get(field):
    query_map = {
        'cell_count': 'SELECT * FROM "Browse_by_cell_line"',
        'animal_count': 'SELECT * FROM "Browse_by_animal_studies"',
        'patient_count': 'SELECT * FROM "Browse_by_Patient_Studies"'
    }

    if field in query_map:
        query = query_map[field]
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
        return df, column_names
    else:
        raise ValueError("Invalid field specified")
