from django.core.management.base import BaseCommand
import pandas as pd
from sqlalchemy import create_engine
import os
from django.conf import settings
from .db_config import engine  # Import the engine from db_config.py

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
