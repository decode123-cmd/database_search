from django.core.management.base import BaseCommand
import pandas as pd
from sqlalchemy import create_engine
import os
from django.conf import settings
import psycopg2
from psycopg2 import OperationalError

# Define the connection URL
connection_url = "postgresql://postgres:ybSxlyKKlCcskPYfuZJwBllGuEyTPmwp@monorail.proxy.rlwy.net:28748/railway"
# Create the SQLAlchemy engine
engine = create_engine(connection_url, echo=False)
print(engine)
def handle(self, *args, **options):
    # Test connection
    try:
        connection = psycopg2.connect(connection_url)
        connection.close()
        self.stdout.write(self.style.SUCCESS('Database connection successful'))
    except OperationalError as e:
        self.stdout.write(self.style.ERROR(f'Error connecting to database: {str(e)}'))



class Command(BaseCommand):
    help = 'Imports data from an Excel file to PostgreSQL'

    def handle(self, *args, **options):
        # Test the database connection

        # Path to the Excel file
        file_path = os.path.join(settings.BASE_DIR, 'master.xlsx')
        
        # Load the Excel file using pandas
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')

        # Iterate over each sheet in the Excel file
        for sheet_name in excel_file.sheet_names:
            # Replace spaces in sheet names with underscores for SQL compatibility
            sheet_name_formatted = sheet_name.replace(' ', '_')
            
            # Load data from the current sheet
            data = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Write data to SQL table
            data.to_sql(sheet_name_formatted, con=engine, if_exists='replace', index=False)
            
            # Output success message
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {sheet_name_formatted}'))
