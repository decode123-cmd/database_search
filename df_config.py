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

# Run a test connection to verify everything works as expected
if __name__ == "__main__":
    test_connection()
