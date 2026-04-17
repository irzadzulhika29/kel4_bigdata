# ingestion/spark_client.py

import os
import urllib.request
from pyspark.sql import SparkSession
from ingestion.config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

def download_required_jars():
    """Mengunduh file JAR secara otomatis untuk koneksi Postgres dan MinIO."""
    jar_dir = "/home/jovyan/work/jars"
    os.makedirs(jar_dir, exist_ok=True)
    
    jars = {
        "postgresql-42.7.1.jar": "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.1/postgresql-42.7.1.jar",
        "hadoop-aws-3.3.4.jar": "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar",
        "aws-java-sdk-bundle-1.12.262.jar": "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar"
    }
    
    jar_paths = []
    for jar_name, url in jars.items():
        jar_path = os.path.join(jar_dir, jar_name)
        jar_paths.append(jar_path)
        
        if not os.path.exists(jar_path):
            print(f"Mengunduh {jar_name}...")
            urllib.request.urlretrieve(url, jar_path)
            print(f" -> Berhasil diunduh!")
            
    return ",".join(jar_paths)

def get_spark_session(app_name="BigData-Processing"):
    """Membuat instance Spark untuk pemrosesan data langsung ke MinIO (Tanpa Hive)."""
    
    local_jars = download_required_jars()
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .master(os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077")) \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "1g") \
        .config("spark.jars", local_jars) \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()
        
    return spark