from django.core.management.base import BaseCommand
import pandas as pd
from sqlalchemy import create_engine
import os
from django.conf import settings


import os
from sqlalchemy import create_engine

# Retrieve environment variables for sensitive settings
db_name = os.getenv('DB_NAME', 'railway')  # Default to 'railway' if not set
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'EiwSTHPfQiMNJHeSEAbsGRLpTIiDvEvT')
db_host = os.getenv('DB_HOST', '${{RAILWAY_PRIVATE_DOMAIN}}')  # Ensure this resolves to an actual host
db_port = os.getenv('DB_PORT', '5432')

# Construct the connection string
connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the SQLAlchemy engine
engine = create_engine(connection_string, echo=False)

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("Database connection successful:", result.scalar())
    except Exception as e:
        print("Database connection failed:", e)
class Command(BaseCommand):
    help = 'Imports data from an Excel file to PostgreSQL'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR,'full_excel.xlsx')
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
       

        for sheet_name in excel_file.sheet_names:
            sheet_name_formatted = sheet_name.replace(' ', '_')
            data = pd.read_excel(excel_file, sheet_name=sheet_name)
            data.to_sql(sheet_name_formatted, con=engine, if_exists='replace', index=False)
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {sheet_name_formatted}'))
