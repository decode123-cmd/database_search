import pandas as pd
import os
import sys
import django
from django.conf import settings
import mysql.connector
from mysql.connector import Error

# Step 0: Add your project directory to the Python path
sys.path.append('/home/gdt-ws4/Documents/praveen_project/cancer_immuno')  # Adjust this path as needed

# Step 1: Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cancer_immuno.settings')  # Adjust if your settings module has a different name

# Step 2: Initialize Django
django.setup()

# Step 3: Read the Excel sheet named "Master"
excel_file = '/home/gdt-ws4/Music/Akshat.xlsx'  # Replace with the path to your Excel file
df = pd.read_excel(excel_file, sheet_name='Master')
df.fillna('Data Not Available', inplace=True)

# Print DataFrame columns to verify
print("DataFrame columns:", df.columns)

# Step 4: Ensure column names are unique by appending a suffix to duplicates
def make_column_names_unique(cols):
    seen = {}
    result = []
    for col in cols:
        # Replace spaces and special characters with underscores
        new_col = col.replace(' ', '_').replace('/', '_').replace('-', '_')
        if new_col in seen:
            seen[new_col] += 1
            new_col = f"{new_col}_{seen[new_col]}"
        else:
            seen[new_col] = 0
        result.append(new_col)
    return result
def insert_query(cols):
    return f"INSERT INTO Master ({', '.join(cols)}) VALUES ({', '.join(['%s' for _ in range(len(cols))])})"

df.columns = make_column_names_unique(df.columns)

# Step 5: Establish a connection to the MySQL database
try:
    host = settings.DATABASES['default']['HOST']
    database = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']

    connection = None

    print("Connecting to MySQL...")
    connection = mysql.connector.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        auth_plugin='mysql_native_password'  # Specify authentication plugin
    )

    if connection.is_connected():
        print("Successfully connected to MySQL")
        cursor = connection.cursor()

        # Create the table with all columns
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS Master (
            {}
        )
        '''.format(', '.join([f'`{col}` VARCHAR(255)' for col in df.columns]))  # Adjust column types as needed

        print("Create table query:", create_table_query)
        cursor.execute(create_table_query)
        connection.commit()

        # Insert DataFrame rows into the table
        for i, row in df.iterrows():
            sql = "INSERT INTO Master (`{}`) VALUES ({})".format(
                '`, `'.join(df.columns),
                ', '.join(['%s'] * len(row))
            )
            print("Insert query:", sql)
            cursor.execute(sql, tuple(row))

        connection.commit()
        print("Data uploaded to MySQL table 'Master'")

except Error as e:
    print("Error while connecting to MySQL", e)

finally:
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
