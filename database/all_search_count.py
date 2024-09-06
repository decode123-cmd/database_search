from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
import pandas as pd
from sqlalchemy import create_engine, text  # Import text from sqlalchemy
import psycopg2

# Database connection parameters
connection_url = "postgresql://postgres:ybSxlyKKlCcskPYfuZJwBllGuEyTPmwp@monorail.proxy.rlwy.net:28748/railway"

# Create the SQLAlchemy engine
engine = create_engine(connection_url, echo=False)

def category():
    try:
        queries = {
            'index': 'SELECT * FROM "Browse_by_index"',
            'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
            'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
            'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
        }
        
        # Use SQLAlchemy's engine to connect and execute queries
        with engine.connect() as connection:
            dataframes = {}
            for key, query in queries.items():
                # Use text() to execute raw SQL queries
                result_proxy = connection.execute(text(query))
                rows = result_proxy.fetchall()
                column_names = result_proxy.keys()
                dataframes[key] = pd.DataFrame(rows, columns=column_names)

            # Extract and process data
            drug_categories = dataframes['index']['Drug category'].unique()
            counts = {
                category: {
                    'Cell_Count': len(dataframes['cell_line'][dataframes['cell_line']['Drug category'] == category]),
                    'Animal_Count': len(dataframes['animal_studies'][dataframes['animal_studies']['Drug category'] == category]),
                    'Patient_Count': len(dataframes['patients'][dataframes['patients']['Drug category'] == category])
                } for category in drug_categories
            }
            
        return counts

    except Exception as e:
        print(f"Error processing request: {e}")  # Log to your server logs
        return {}

def techniques():
    try:
        queries = {
            'index': 'SELECT * FROM "Browse_by_index"',
            'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
            'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
            'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
        }
        
        with engine.connect() as connection:
            dataframes = {}
            for key, query in queries.items():
                result_proxy = connection.execute(text(query))  # Use text() here
                rows = result_proxy.fetchall()  
                column_names = result_proxy.keys()
                dataframes[key] = pd.DataFrame(rows, columns=column_names)

            # Process technique data
            drug_categories = dataframes['index']['Technique'].dropna().unique()  # Drop None values before finding unique
            search_terms = {}

            for category in drug_categories:
                terms = [term.strip() for term in category.split('/')]
                search_terms[category] = terms

            counts = {}

            for category, terms in search_terms.items():
                counts[category] = {
                    'Cell_Count': int(dataframes['cell_line']['Technique'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum()),
                    'Animal_Count': int(dataframes['animal_studies']['Technique'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum()),
                    'Patient_Count': int(dataframes['patients']['Technique'].apply(lambda x: any(term.lower() in str(x).lower() for term in terms) if x is not None else False).sum())
                }

            return counts

    except Exception as e:
        print(f"Error processing request: {e}")
        return {}

def cancer():
    try:
        queries = {
            'index': 'SELECT * FROM "Browse_by_index"',
            'cell_line': 'SELECT * FROM "Browse_by_cell_line"',
            'animal_studies': 'SELECT * FROM "Browse_by_animal_studies"',
            'patients': 'SELECT * FROM "Browse_by_Patient_Studies"'
        }
        
        with engine.connect() as connection:
            dataframes = {}
            for key, query in queries.items():
                result_proxy = connection.execute(text(query))  # Use text() here
                rows = result_proxy.fetchall()
                column_names = result_proxy.keys()
                dataframes[key] = pd.DataFrame(rows, columns=column_names)

            # Extract cancer type data
            drug_categories = dataframes['index']['Cancer_Type'].unique()
            counts = {
                category: {
                    'Cell_Count': len(dataframes['cell_line'][dataframes['cell_line']['Cancer_Type'] == category]),
                    'Animal_Count': len(dataframes['animal_studies'][dataframes['animal_studies']['Cancer_Type'] == category]),
                    'Patient_Count': len(dataframes['patients'][dataframes['patients']['Cancer_Type'] == category])
                } for category in drug_categories
            }
            
        return counts

    except Exception as e:
        print(f"Error processing request: {e}")
        return {}

def data_get(field):
    query_map = {
        'cell_count': 'SELECT * FROM "Browse_by_cell_line"',
        'animal_count': 'SELECT * FROM "Browse_by_animal_studies"',
        'patient_count': 'SELECT * FROM "Browse_by_Patient_Studies"'
    }

    if field in query_map:
        query = query_map[field]
        with engine.connect() as connection:
            result_proxy = connection.execute(text(query))  # Use text() here
            rows = result_proxy.fetchall()
            column_names = result_proxy.keys()
            df = pd.DataFrame(rows, columns=column_names)
        return df, column_names
    else:
        raise ValueError("Invalid field specified")
