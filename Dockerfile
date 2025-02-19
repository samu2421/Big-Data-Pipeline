# Use the official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy everything into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install psycopg2-binary pymongo pandas sqlalchemy

# Set the entry point
CMD ["python", "data_ingestion.py"]
