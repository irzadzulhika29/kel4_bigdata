# ingestion/config.py

import os

# Konfigurasi Direktori
TARGET_DIR = os.environ.get("DATA_DIR", "/home/jovyan/work/data/dataset")

# Konfigurasi PostgreSQL
_pg_host = os.environ.get("POSTGRES_HOST", "postgres")
_pg_db   = os.environ.get("POSTGRES_DB", "odoo_erp")
DB_URL = f"jdbc:postgresql://{_pg_host}:5432/{_pg_db}"
DB_PROPERTIES = {
    "user":     os.environ.get("POSTGRES_USER", "admin"),
    "password": os.environ.get("POSTGRES_PASSWORD", "adminpassword"),
    "driver":   "org.postgresql.Driver",
}

# Konfigurasi MinIO (S3)
MINIO_ENDPOINT   = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
