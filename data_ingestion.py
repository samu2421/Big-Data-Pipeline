import os
import pandas as pd
from sqlalchemy import create_engine
from pymongo import MongoClient

# Get the DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://samiksha:password123@postgres:5432/ecommerce_data")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")  # Use local MongoDB if not running in Docker
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["OnlineRetail"]
mongo_collection = mongo_db["unstructured_data"]

# CSV file path
csv_file_path = "dataset.csv"
df = pd.read_csv(csv_file_path)

# Read CSV in chunks (batch size = 1000 rows)
batch_size = 1000
for chunk in pd.read_csv(csv_file_path, delimiter=',', chunksize=batch_size):
    # Convert InvoiceDate to timestamp
    chunk["InvoiceDate"] = pd.to_datetime(chunk["InvoiceDate"], format='%d/%m/%y %H:%M', errors='coerce')

    # Convert column names to match the database schema
    chunk.columns = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']

    # Insert batch into PostgreSQL
    chunk.to_sql("sales_data", engine, if_exists="append", index=False)
    print(f"{len(chunk)} rows inserted into PostgreSQL...")

    # Convert batch to dictionary format and insert into MongoDB
    data_dict = chunk.to_dict(orient="records")
    mongo_collection.insert_many(data_dict)
    print(f"{len(data_dict)} records inserted into MongoDB...")

print("Batch data ingestion completed successfully!")
