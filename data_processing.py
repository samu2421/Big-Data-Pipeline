import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["OnlineRetail"]
collection = db["unstructured_data"]

# Fetch all records
cursor = collection.find()
df = pd.DataFrame(list(cursor))

# Drop MongoDB `_id` column
df.drop(columns=["_id"], inplace=True, errors="ignore")

# Debug: Print columns
print("Columns in the DataFrame:", df.columns)

# Data Transformations
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']  # Compute total price per transaction
df['InvoiceYearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
df_filtered = df[df['TotalPrice'] > 100]  # Filter transactions where TotalPrice > 100
df_grouped = df.groupby(['InvoiceYearMonth', 'Country']).agg({'TotalPrice': 'sum'}).reset_index()  # Aggregate sales by month and country

# Display processed data
print("Filtered Data:\n", df_filtered.head())
print("\nGrouped Data:\n", df_grouped.head())

# Save processed data back to MongoDB (optional)
collection_processed = db["processed_data"]
collection_processed.insert_many(df_grouped.to_dict(orient="records"))

print("Data processing completed successfully!")
