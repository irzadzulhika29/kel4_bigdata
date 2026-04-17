def load_bronze_data(spark):
    """Membaca tiga tabel Bronze Layer dari MinIO."""
    print("[Silver] Membaca data Bronze...")
    sales     = spark.read.parquet("s3a://bronze/sales")
    customers = spark.read.parquet("s3a://bronze/customers")
    items     = spark.read.parquet("s3a://bronze/items")
    return sales, customers, items

def save_to_silver_minio(df, spark):
    """Menyimpan DataFrame ke bucket silver sebagai Parquet berpartisi per tahun."""
    print("[Silver] Menyimpan ke MinIO dengan Partisi Tahun...")
    output_path = "s3a://silver/integrated_sales"
    df.write \
        .mode("overwrite") \
        .partitionBy("year") \
        .parquet(output_path)
    print(f"🎉 Layer Silver Berhasil Disimpan di: {output_path}")
