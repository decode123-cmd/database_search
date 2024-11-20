from django.core.management.base import BaseCommand
import pandas as pd
from sqlalchemy import create_engine
import os
from django.conf import settings
import psycopg2
from psycopg2 import OperationalError

# Define the connection URL
connection_url = "postgresql://postgres:OvRIsbhSnGIHWFDawjJaEBTiESwdXZKY@autorack.proxy.rlwy.net:24342/railway"

# Create the SQLAlchemy engine
engine = create_engine(connection_url, echo=False)

class Command(BaseCommand):
    help = 'Imports data from an Excel file to PostgreSQL'

    def handle(self, *args, **options):
        # Test the database connection
        try:
            connection = psycopg2.connect(connection_url)
            connection.close()
            self.stdout.write(self.style.SUCCESS('Database connection successful'))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to database: {str(e)}'))
            return
        
        # Path to the Excel file
        file_path = os.path.join(settings.BASE_DIR, 'Akshat.xlsx')
        
        # Load the Excel file using pandas
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')

        # Iterate over each sheet in the Excel file
        for sheet_name in excel_file.sheet_names:
            # Replace spaces in sheet names with underscores for SQL compatibility
            sheet_name_formatted = sheet_name.replace(' ', '_')
            
            # Load data from the current sheet
            data = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Drop unnamed columns (columns with no headers)
            data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
            
            # Ensure all column names are valid for SQL
            data.columns = [col.strip().replace(' ', '_') for col in data.columns]
            
            # Write data to SQL table
            try:
                data.to_sql(sheet_name_formatted, con=engine, if_exists='replace', index=False)
                self.stdout.write(self.style.SUCCESS(f'Successfully imported {sheet_name_formatted}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {sheet_name_formatted}: {str(e)}'))
