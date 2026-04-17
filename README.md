# Big Data Project

Pipeline data engineering dan analytics berbasis Docker untuk memproses data retail sintetis ke arsitektur `bronze -> silver -> gold` menggunakan PostgreSQL, MinIO, Spark, dan Jupyter Notebook.

## Ringkasan

Project ini menjalankan alur berikut:

1. `customers` disimpan dan di-seed ke PostgreSQL.
2. `sales_1m.csv` dan `items.csv` dibaca ke Spark.
3. Data mentah dimuat ke MinIO sebagai Bronze layer.
4. Data dibersihkan, di-join, dan dipartisi ke Silver layer.
5. Data Silver dipakai untuk:
   - segmentasi pelanggan RFM di Gold layer
   - analisis churn dengan Random Forest

## Stack

- Docker Compose
- PostgreSQL 13
- MinIO
- Spark 3.5
- Jupyter PySpark Notebook
- PySpark

## Prasyarat

- Docker
- Docker Compose
- RAM yang cukup untuk menjalankan Spark + Jupyter + PostgreSQL + MinIO

Opsional:

- Akses internet dari container Jupyter untuk mengunduh dataset dari folder Google Drive publik

## Setup

1. Clone repo lalu masuk ke folder project.
2. Salin file environment:

```bash
cp .env.example .env
```

3. Jalankan seluruh service:

```bash
docker compose up -d
```

4. Pastikan container aktif:

```bash
docker compose ps
```

## Konfigurasi Environment

File `.env.example` sudah berisi nilai default berikut:

- `POSTGRES_USER=admin`
- `POSTGRES_PASSWORD=adminpassword`
- `POSTGRES_DB=odoo_erp`
- `MINIO_ROOT_USER=minioadmin`
- `MINIO_ROOT_PASSWORD=minioadmin`
- `SPARK_MASTER_URL=spark://spark-master:7077`
- `JUPYTER_PORT=8888`
- `JUPYTER_TOKEN=bigdata2024`

Biasanya tidak perlu diubah untuk local development.

## Service dan Port

- PostgreSQL: `localhost:5432`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Spark Master UI: `http://localhost:8080`
- Spark Master endpoint: `spark://localhost:7077`
- Jupyter Notebook: `http://localhost:8888`

Login Jupyter menggunakan token dari `JUPYTER_TOKEN`.

## Menjalankan Pipeline

Setelah `docker compose up -d`, buka Jupyter:

```text
http://localhost:8888/?token=bigdata2024
```

Jalankan notebook secara berurutan:

1. `notebooks/01_main_ingestion.ipynb`
2. `notebooks/02_processing_silver.ipynb`
3. `notebooks/03_analysis_rfm_gold.ipynb`
4. `notebooks/03_analysis_churn_gold.ipynb`

### 1. Ingestion ke Bronze

Notebook: [notebooks/01_main_ingestion.ipynb](/home/irzadzulhika/Dev/bigdata_project/notebooks/01_main_ingestion.ipynb)

Yang dilakukan:

- install dependency Python di environment Jupyter bila diperlukan
- cek / unduh `customers.csv`, `items.csv`, dan `sales_1m.csv` dari folder Google Drive
- buat Spark session
- validasi tabel `customers` di PostgreSQL
- muat data ke MinIO bucket `bronze`

Output utama:

- `s3a://bronze/customers`
- `s3a://bronze/sales`
- `s3a://bronze/items`

### 2. Processing ke Silver

Notebook: [notebooks/02_processing_silver.ipynb](/home/irzadzulhika/Dev/bigdata_project/notebooks/02_processing_silver.ipynb)

Transformasi yang dilakukan:

- hapus duplikat
- drop baris tanpa `customer_id`
- join `sales + customers + items`
- hitung ulang `revenue = quantity * unit_price`
- tambah kolom partisi `year`

Output utama:

- `s3a://silver/integrated_sales`

### 3. Gold Layer RFM

Notebook: [notebooks/03_analysis_rfm_gold.ipynb](/home/irzadzulhika/Dev/bigdata_project/notebooks/03_analysis_rfm_gold.ipynb)

Yang dilakukan:

- load data Silver
- hitung metrik `recency`, `frequency`, `monetary`
- normalisasi fitur
- pilih jumlah cluster
- segmentasi pelanggan dengan K-Means

Output utama:

- `s3a://gold/rfm_segments`

### 4. Analisis Churn

Notebook: [notebooks/03_analysis_churn_gold.ipynb](/home/irzadzulhika/Dev/bigdata_project/notebooks/03_analysis_churn_gold.ipynb)

Yang dilakukan:

- load hasil RFM dari Gold
- gabungkan fitur profil pelanggan dari Silver
- label churn berdasarkan `recency > 90`
- training Random Forest
- evaluasi model dan visualisasi insight bisnis

Catatan:

- notebook ini fokus ke analisis dan evaluasi
- model belum disimpan sebagai artifact terpisah di repo

## Struktur Folder

```text
bigdata_project/
├── docker-compose.yml
├── .env.example
├── data/
│   └── dataset/
│       ├── sales_1m.csv
│       ├── customers.csv
│       └── items.csv
├── init-sql/
│   ├── init.sql
│   └── seed_customers.sh
├── jars/
│   ├── postgresql-42.7.1.jar
│   ├── hadoop-aws-3.3.4.jar
│   └── aws-java-sdk-bundle-1.12.262.jar
├── notebooks/
│   ├── 01_main_ingestion.ipynb
│   ├── 02_processing_silver.ipynb
│   ├── 03_analysis_rfm_gold.ipynb
│   ├── 03_analysis_churn_gold.ipynb
│   ├── ingestion/
│   │   ├── config.py
│   │   ├── downloader.py
│   │   ├── etl_bronze.py
│   │   └── spark_client.py
│   └── processing/
│       └── etl_silver.py
└── README.md
```

## Penjelasan Folder

- `data/dataset/`: sumber data CSV lokal
- `init-sql/`: inisialisasi database dan script seed PostgreSQL
- `jars/`: dependency JDBC dan S3A untuk koneksi Spark ke PostgreSQL dan MinIO
- `notebooks/`: entry point notebook untuk pipeline dan analisis
- `notebooks/ingestion/`: helper module untuk ingestion Bronze
- `notebooks/processing/`: helper module untuk transformasi Silver
- `postgres_data/`: volume database lokal hasil Docker, tidak perlu dikomit

## Alur Data Singkat

```text
customers.csv -> PostgreSQL -----------+
                                       |
sales_1m.csv --------------------------+--> Bronze (MinIO)
                                       |
items.csv -----------------------------+

Bronze --> Silver (cleaning, join, partition)
Silver --> Gold RFM (K-Means segmentation)
Silver + Gold RFM --> Churn Analysis (Random Forest)
```

## Catatan Teknis

- Bucket MinIO `bronze`, `silver`, dan `gold` dibuat otomatis oleh service `minio-init`.
- Tabel `customers` dibuat dan di-seed otomatis oleh service `postgres-seed`.
- `spark_client.py` akan memastikan JAR yang dibutuhkan tersedia di `/home/jovyan/work/jars`.
- Helper downloader akan menarik seluruh isi folder Google Drive publik dan memastikan tiga file wajib tersedia: `customers.csv`, `items.csv`, dan `sales_1m.csv`.

## Verifikasi Cepat

Perintah yang umum dipakai:

```bash
docker compose ps
docker compose logs -f postgres-seed
docker compose logs -f minio-init
docker compose logs -f jupyter
```

## Stop Project

Untuk menghentikan service:

```bash
docker compose down
```

Untuk menghentikan dan menghapus volume database lokal:

```bash
docker compose down -v
```

Gunakan `-v` hanya jika memang ingin reset data PostgreSQL lokal.
