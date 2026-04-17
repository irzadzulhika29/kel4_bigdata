# ingestion/etl_bronze.py

import os

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
from ingestion.config import TARGET_DIR, DB_URL, DB_PROPERTIES

SALES_SOURCE_FILE = f"{TARGET_DIR}/sales_1m.csv"


def seed_postgresql(spark):
    """Memastikan tabel customers hasil seed Docker sudah tersedia di PostgreSQL."""
    print("\n[Step 1] Mengecek tabel 'customers' di PostgreSQL...")

    try:
        customers_count_df = spark.read.jdbc(
            url=DB_URL,
            table="(SELECT COUNT(*) AS total_rows FROM customers) AS customers_count",
            properties=DB_PROPERTIES
        )
        total_rows = customers_count_df.collect()[0]["total_rows"]
    except Exception as exc:
        raise RuntimeError(
            "Tabel 'customers' belum tersedia di PostgreSQL. Jalankan docker compose up terlebih dahulu agar service postgres-seed memuat customers.csv."
        ) from exc

    print(f"-> Tabel 'customers' siap dipakai di PostgreSQL dengan {total_rows} baris.")

def load_to_minio_bronze(spark):
    """Menarik data dari PostgreSQL dan CSV, lalu menyimpannya ke MinIO format Parquet."""
    print("\n[Step 2] Memulai proses Data Ingestion ke MinIO (Layer Bronze)...")

    # A. Postgres -> MinIO (Customers)
    print("  -> Menarik tabel 'customers' dari PostgreSQL...")
    customers_pg_df = spark.read.jdbc(url=DB_URL, table="customers", properties=DB_PROPERTIES)
    customers_pg_df.write.parquet("s3a://bronze/customers", mode="overwrite")

    # ==========================================================
    # B. CSV -> MinIO (Sales 1M Sample)
    # ==========================================================
    if not os.path.exists(SALES_SOURCE_FILE):
        raise RuntimeError(
            f"File sample sales belum tersedia di {SALES_SOURCE_FILE}. Siapkan sales_1m.csv terlebih dahulu."
        )

    print("  -> Membaca 'sales_1m.csv' dengan Explicit Schema...")
    
    # 1. Skema Akurat Sesuai Profiling Data Asli
    sales_schema = StructType([
        StructField("invoice_id", StringType(), True),
        StructField("customer_id", IntegerType(), True),
        StructField("invoice_date", DateType(), True),
        StructField("product_id", IntegerType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("revenue", DoubleType(), True),
        StructField("store_id", IntegerType(), True)
    ])

    # 2. Baca CSV tanpa inferSchema agar super cepat (Single-Pass)
    sales_df = spark.read.csv(
        SALES_SOURCE_FILE,
        header=True, 
        schema=sales_schema
    )
    sales_df.repartition(12).write.parquet("s3a://bronze/sales", mode="overwrite")
    print("  -> Sukses disimpan di MinIO: s3a://bronze/sales")

    # C. CSV -> MinIO (Items)
    # (Items biasanya ukurannya kecil, jadi inferSchema masih aman)
    print("  -> Membaca 'items.csv'...")
    items_df = spark.read.csv(f"{TARGET_DIR}/items.csv", header=True, inferSchema=True)
    items_df.write.parquet("s3a://bronze/items", mode="overwrite")

    print("\n🎉 SELAMAT! Pipeline Ingestion Tahap 1 (Bronze Layer) Selesai!")
