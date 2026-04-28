# Dokumentasi Pipeline Big Data Project
## Kelompok 4 - Tugas Kuliah Big Data

---

## 📋 Daftar Isi

1. [Ringkasan Project](#ringkasan-project)
2. [Arsitektur Pipeline](#arsitektur-pipeline)
3. [Teknologi yang Digunakan](#teknologi-yang-digunakan)
4. [Struktur Project](#struktur-project)
5. [Alur Data Pipeline](#alur-data-pipeline)
6. [Instalasi dan Setup](#instalasi-dan-setup)
7. [Menjalankan Pipeline](#menjalankan-pipeline)
8. [Penjelasan Setiap Layer](#penjelasan-setiap-layer)
9. [Monitoring dan Troubleshooting](#monitoring-dan-troubleshooting)
10. [Kesimpulan](#kesimpulan)

---

## 🎯 Ringkasan Project

Project ini merupakan implementasi pipeline data engineering dan analytics berbasis Docker untuk memproses data retail sintetis menggunakan arsitektur **Medallion Architecture** (Bronze → Silver → Gold).

### Tujuan Project:
- Membangun pipeline ETL (Extract, Transform, Load) yang scalable
- Mengimplementasikan data lake dengan MinIO sebagai object storage
- Melakukan data processing menggunakan Apache Spark
- Menghasilkan insights bisnis melalui analisis RFM dan prediksi churn

### Dataset:
- **customers.csv**: Data pelanggan (dari PostgreSQL)
- **sales_1m.csv**: Data transaksi penjualan (1 juta records)
- **items.csv**: Data produk/item

---

## 🏗️ Arsitektur Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (customers)  │  CSV Files (sales, items)            │
└────────────┬─────────────┴──────────────────┬───────────────────┘
             │                                 │
             └─────────────┬───────────────────┘
                           │
                           ▼
             ┌─────────────────────────────┐
             │    BRONZE LAYER (MinIO)     │
             │   - Raw Data Storage        │
             │   - No Transformation       │
             └──────────────┬──────────────┘
                           │
                           ▼
             ┌─────────────────────────────┐
             │    SILVER LAYER (MinIO)     │
             │   - Data Cleaning           │
             │   - Data Integration        │
             │   - Data Partitioning       │
             └──────────────┬──────────────┘
                           │
                           ▼
             ┌─────────────────────────────┐
             │     GOLD LAYER (MinIO)      │
             │   - RFM Segmentation        │
             │   - Churn Analysis          │
             │   - Business Insights       │
             └─────────────────────────────┘
```

---

## 🛠️ Teknologi yang Digunakan

### Infrastructure & Orchestration
- **Docker & Docker Compose**: Containerization dan orchestration
- **PostgreSQL 13**: Relational database untuk data pelanggan
- **MinIO**: S3-compatible object storage (pengganti HDFS)

### Data Processing
- **Apache Spark 3.5**: Distributed data processing engine
- **PySpark**: Python API untuk Spark
- **Jupyter Notebook**: Interactive development environment

### Machine Learning
- **Scikit-learn**: Machine learning library untuk clustering dan classification
- **K-Means**: Customer segmentation
- **Random Forest**: Churn prediction

### Visualization
- **Matplotlib**: Data visualization
- **Seaborn**: Statistical data visualization

---

## 📁 Struktur Project

```
kel4_bigdata/
│
├── docker-compose.yml              # Konfigurasi semua services
├── .env                            # Environment variables
├── .env.example                    # Template environment variables
├── README.md                       # Dokumentasi singkat
├── DOKUMENTASI_PIPELINE.md         # Dokumentasi lengkap (file ini)
│
├── data/                           # Data source
│   └── dataset/
│       ├── customers.csv           # Data pelanggan
│       ├── sales_1m.csv            # Data transaksi (1M records)
│       └── items.csv               # Data produk
│
├── init-sql/                       # Database initialization
│   ├── init.sql                    # Schema database
│   └── seed_customers.sh           # Script untuk seed data customers
│
├── jars/                           # Spark dependencies
│   ├── postgresql-42.7.1.jar       # JDBC driver PostgreSQL
│   ├── hadoop-aws-3.3.4.jar        # Hadoop AWS connector
│   └── aws-java-sdk-bundle-1.12.262.jar  # AWS SDK
│
├── notebooks/                      # Jupyter notebooks
│   ├── 01_main_ingestion.ipynb     # Bronze layer ingestion
│   ├── 02_processing_silver.ipynb  # Silver layer processing
│   ├── 03_analysis_rfm_gold.ipynb  # RFM segmentation
│   ├── 03_analysis_churn_gold.ipynb # Churn analysis
│   │
│   ├── ingestion/                  # Helper modules untuk ingestion
│   │   ├── config.py               # Konfigurasi koneksi
│   │   ├── downloader.py           # Download dataset
│   │   ├── etl_bronze.py           # ETL logic untuk Bronze
│   │   └── spark_client.py         # Spark session management
│   │
│   └── processing/                 # Helper modules untuk processing
│       └── etl_silver.py           # ETL logic untuk Silver
│
└── postgres_data/                  # PostgreSQL data volume (auto-generated)
```

---

## 🔄 Alur Data Pipeline

### 1️⃣ **Bronze Layer - Data Ingestion**

**Tujuan**: Menyimpan raw data tanpa transformasi

**Proses**:
```
PostgreSQL (customers) ──┐
                         │
CSV Files (sales)    ────┼──> Spark ──> MinIO (s3a://bronze/)
                         │
CSV Files (items)    ────┘
```

**Output**:
- `s3a://bronze/customers/` - Data pelanggan
- `s3a://bronze/sales/` - Data transaksi
- `s3a://bronze/items/` - Data produk

**Karakteristik**:
- Data disimpan dalam format Parquet
- Tidak ada transformasi atau cleaning
- Schema validation minimal
- Append-only storage

---

### 2️⃣ **Silver Layer - Data Processing**

**Tujuan**: Membersihkan, mengintegrasikan, dan menyiapkan data untuk analisis

**Proses**:
```
Bronze Layer ──> Spark Processing ──> Silver Layer
                      │
                      ├─ Remove duplicates
                      ├─ Handle missing values
                      ├─ Join tables (sales + customers + items)
                      ├─ Calculate derived columns
                      └─ Partition by year
```

**Transformasi yang Dilakukan**:

1. **Data Cleaning**:
   - Hapus duplikat berdasarkan `transaction_id`
   - Drop baris dengan `customer_id` null
   - Validasi tipe data

2. **Data Integration**:
   ```sql
   SELECT 
       s.transaction_id,
       s.customer_id,
       c.customer_name,
       c.email,
       c.country,
       s.item_id,
       i.item_name,
       i.category,
       s.quantity,
       i.unit_price,
       (s.quantity * i.unit_price) as revenue,
       s.transaction_date,
       YEAR(s.transaction_date) as year
   FROM sales s
   JOIN customers c ON s.customer_id = c.customer_id
   JOIN items i ON s.item_id = i.item_id
   ```

3. **Data Partitioning**:
   - Partisi berdasarkan `year` untuk optimasi query

**Output**:
- `s3a://silver/integrated_sales/` - Data terintegrasi dan bersih

---

### 3️⃣ **Gold Layer - Analytics & Insights**

#### A. RFM Segmentation (Customer Segmentation)

**Tujuan**: Mengelompokkan pelanggan berdasarkan perilaku pembelian

**Metrik RFM**:
- **Recency (R)**: Berapa lama sejak transaksi terakhir?
- **Frequency (F)**: Berapa sering pelanggan bertransaksi?
- **Monetary (M)**: Berapa total nilai transaksi pelanggan?

**Proses**:
```
Silver Layer ──> Calculate RFM Metrics ──> Normalize ──> K-Means Clustering ──> Gold Layer
```

**Implementasi**:
```python
# Calculate RFM
rfm = df.groupBy("customer_id").agg(
    F.datediff(F.current_date(), F.max("transaction_date")).alias("recency"),
    F.count("transaction_id").alias("frequency"),
    F.sum("revenue").alias("monetary")
)

# Normalize features
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm)

# K-Means Clustering
kmeans = KMeans(n_clusters=4, random_state=42)
segments = kmeans.fit_predict(rfm_scaled)
```

**Output**:
- `s3a://gold/rfm_segments/` - Customer segments dengan label cluster

**Interpretasi Segments**:
- **Cluster 0**: Champions (High F, High M, Low R)
- **Cluster 1**: At Risk (High R, Low F)
- **Cluster 2**: Loyal Customers (Medium R, High F)
- **Cluster 3**: New Customers (Low F, Low M)

---

#### B. Churn Analysis (Prediksi Customer Churn)

**Tujuan**: Memprediksi pelanggan yang berpotensi churn

**Definisi Churn**: Pelanggan yang tidak bertransaksi > 90 hari

**Proses**:
```
Silver + Gold (RFM) ──> Feature Engineering ──> Train/Test Split ──> Random Forest ──> Evaluation
```

**Features yang Digunakan**:
- Recency, Frequency, Monetary (dari RFM)
- Country (encoded)
- RFM Segment (dari clustering)
- Transaction patterns

**Implementasi**:
```python
# Label churn
df['is_churn'] = (df['recency'] > 90).astype(int)

# Feature engineering
features = ['recency', 'frequency', 'monetary', 'country_encoded', 'rfm_segment']
X = df[features]
y = df['is_churn']

# Train model
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Evaluate
accuracy = rf_model.score(X_test, y_test)
```

**Output**:
- Model evaluation metrics (accuracy, precision, recall, F1-score)
- Feature importance visualization
- Business insights dan rekomendasi

---

## 🚀 Instalasi dan Setup

### Prasyarat

1. **Docker Desktop** (Windows/Mac) atau **Docker Engine** (Linux)
   - Minimum RAM: 8GB
   - Recommended RAM: 16GB

2. **Docker Compose** (biasanya sudah include di Docker Desktop)

3. **Git** (untuk clone repository)

### Langkah Instalasi

#### 1. Clone Repository
```bash
git clone <repository-url>
cd kel4_bigdata
```

#### 2. Setup Environment Variables
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

#### 3. Verifikasi File Dataset
Pastikan file-file berikut ada di folder `data/dataset/`:
- `customers.csv`
- `sales_1m.csv`
- `items.csv`

#### 4. Start All Services
```bash
docker compose up -d
```

#### 5. Verifikasi Services
```bash
docker compose ps
```

Output yang diharapkan:
```
NAME                    STATUS
bigdata-db              Up (healthy)
bigdata-db-seed         Exited (0)
bigdata-minio           Up
bigdata-minio-init      Exited (0)
bigdata-spark-master    Up
bigdata-spark-worker    Up
bigdata-jupyter         Up
```

---

## ▶️ Menjalankan Pipeline

### 1. Akses Jupyter Notebook

Buka browser dan akses:
```
http://localhost:8888/?token=bigdata2024
```

### 2. Jalankan Notebooks Secara Berurutan

#### Step 1: Bronze Layer Ingestion
**Notebook**: `01_main_ingestion.ipynb`

**Yang dilakukan**:
- Install dependencies Python
- Download dataset (jika belum ada)
- Validasi koneksi ke PostgreSQL
- Load data ke MinIO bucket `bronze`

**Cara menjalankan**:
1. Buka notebook `01_main_ingestion.ipynb`
2. Klik menu `Kernel` → `Restart & Run All`
3. Tunggu hingga semua cell selesai dieksekusi
4. Verifikasi output: "✅ Data berhasil dimuat ke Bronze layer"

**Waktu eksekusi**: ~5-10 menit (tergantung ukuran dataset)

---

#### Step 2: Silver Layer Processing
**Notebook**: `02_processing_silver.ipynb`

**Yang dilakukan**:
- Load data dari Bronze layer
- Data cleaning (remove duplicates, handle nulls)
- Data integration (join sales + customers + items)
- Calculate derived columns (revenue)
- Partition by year
- Save to Silver layer

**Cara menjalankan**:
1. Buka notebook `02_processing_silver.ipynb`
2. Klik menu `Kernel` → `Restart & Run All`
3. Tunggu hingga semua cell selesai dieksekusi
4. Verifikasi output: "✅ Data berhasil diproses ke Silver layer"

**Waktu eksekusi**: ~10-15 menit

---

#### Step 3: Gold Layer - RFM Segmentation
**Notebook**: `03_analysis_rfm_gold.ipynb`

**Yang dilakukan**:
- Load data dari Silver layer
- Calculate RFM metrics
- Normalize features
- Determine optimal number of clusters (Elbow method)
- K-Means clustering
- Save segments to Gold layer
- Visualize customer segments

**Cara menjalankan**:
1. Buka notebook `03_analysis_rfm_gold.ipynb`
2. Klik menu `Kernel` → `Restart & Run All`
3. Tunggu hingga semua cell selesai dieksekusi
4. Review visualisasi dan insights

**Output visualisasi**:
- Elbow curve untuk optimal K
- Customer segmentation map
- Segment characteristics table

**Waktu eksekusi**: ~5-8 menit

---

#### Step 4: Gold Layer - Churn Analysis
**Notebook**: `03_analysis_churn_gold.ipynb`

**Yang dilakukan**:
- Load data dari Silver dan Gold (RFM)
- Feature engineering
- Label churn customers
- Train/test split
- Train Random Forest model
- Model evaluation
- Feature importance analysis
- Business insights

**Cara menjalankan**:
1. Buka notebook `03_analysis_churn_gold.ipynb`
2. Klik menu `Kernel` → `Restart & Run All`
3. Tunggu hingga semua cell selesai dieksekusi
4. Review model performance dan insights

**Output**:
- Model accuracy, precision, recall, F1-score
- Confusion matrix
- Feature importance chart
- Business recommendations

**Waktu eksekusi**: ~8-12 menit

---

## 📊 Penjelasan Setiap Layer

### Bronze Layer (Raw Data)

**Karakteristik**:
- Data mentah tanpa transformasi
- Schema validation minimal
- Immutable (append-only)
- Format: Parquet (compressed)

**Struktur Data**:

**customers**:
```
customer_id | customer_name | email | country | registration_date
```

**sales**:
```
transaction_id | customer_id | item_id | quantity | transaction_date
```

**items**:
```
item_id | item_name | category | unit_price
```

---

### Silver Layer (Cleaned & Integrated)

**Karakteristik**:
- Data bersih dan terintegrasi
- Schema enforcement
- Partitioned untuk optimasi
- Format: Parquet (partitioned by year)

**Struktur Data**:

**integrated_sales**:
```
transaction_id | customer_id | customer_name | email | country |
item_id | item_name | category | quantity | unit_price | revenue |
transaction_date | year
```

**Partitioning Strategy**:
```
silver/integrated_sales/
├── year=2023/
│   └── part-00000.parquet
├── year=2024/
│   └── part-00000.parquet
└── year=2025/
    └── part-00000.parquet
```

---

### Gold Layer (Analytics & Insights)

**Karakteristik**:
- Data siap untuk business intelligence
- Aggregated dan enriched
- Optimized untuk query performance
- Format: Parquet

**Struktur Data**:

**rfm_segments**:
```
customer_id | customer_name | email | country |
recency | frequency | monetary | rfm_segment |
segment_label | segment_description
```

**Segment Labels**:
- **Champions**: Best customers (High F, High M, Low R)
- **Loyal Customers**: Regular buyers (Medium R, High F)
- **At Risk**: Haven't purchased recently (High R)
- **New Customers**: Recent first-time buyers (Low F)

---

## 🔍 Monitoring dan Troubleshooting

### Monitoring Services

#### 1. PostgreSQL
```bash
# Check logs
docker compose logs postgres

# Connect to database
docker exec -it bigdata-db psql -U admin -d odoo_erp

# Query customers table
SELECT COUNT(*) FROM customers;
```

#### 2. MinIO
**Console**: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

**Verifikasi buckets**:
- bronze
- silver
- gold

#### 3. Spark Master UI
**URL**: http://localhost:8080

**Informasi yang ditampilkan**:
- Active workers
- Running applications
- Completed applications
- Resource usage

#### 4. Jupyter Notebook
**URL**: http://localhost:8888/?token=bigdata2024

**Check logs**:
```bash
docker compose logs jupyter
```

---

### Common Issues & Solutions

#### Issue 1: Container tidak start
**Symptom**: `docker compose ps` menunjukkan status `Exited` atau `Restarting`

**Solution**:
```bash
# Check logs
docker compose logs <service-name>

# Restart specific service
docker compose restart <service-name>

# Restart all services
docker compose down
docker compose up -d
```

---

#### Issue 2: Out of Memory
**Symptom**: Spark job failed dengan error `OutOfMemoryError`

**Solution**:
1. Edit `.env` file:
```bash
SPARK_WORKER_MEMORY=8G  # Increase from 4G to 8G
```

2. Restart services:
```bash
docker compose down
docker compose up -d
```

---

#### Issue 3: Cannot connect to PostgreSQL
**Symptom**: Error `Connection refused` atau `FATAL: password authentication failed`

**Solution**:
1. Verify PostgreSQL is healthy:
```bash
docker compose ps postgres
```

2. Check credentials in `.env`:
```bash
POSTGRES_USER=admin
POSTGRES_PASSWORD=adminpassword
POSTGRES_DB=odoo_erp
```

3. Test connection:
```bash
docker exec -it bigdata-db psql -U admin -d odoo_erp -c "SELECT 1;"
```

---

#### Issue 4: MinIO bucket not found
**Symptom**: Error `NoSuchBucket` saat akses MinIO

**Solution**:
1. Check minio-init logs:
```bash
docker compose logs minio-init
```

2. Manually create buckets:
```bash
docker exec -it bigdata-minio-init mc alias set myminio http://minio:9000 minioadmin minioadmin
docker exec -it bigdata-minio-init mc mb myminio/bronze
docker exec -it bigdata-minio-init mc mb myminio/silver
docker exec -it bigdata-minio-init mc mb myminio/gold
```

---

#### Issue 5: Jupyter kernel keeps dying
**Symptom**: Kernel crashes saat menjalankan Spark job

**Solution**:
1. Increase Docker memory limit (Docker Desktop Settings)
2. Reduce Spark worker memory in `.env`
3. Process data in smaller batches

---

### Performance Tuning

#### Spark Configuration
Edit `notebooks/ingestion/spark_client.py`:

```python
spark = SparkSession.builder \
    .appName("BigDataPipeline") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.default.parallelism", "100") \
    .getOrCreate()
```

#### MinIO Performance
- Use partitioning untuk large datasets
- Enable compression (Parquet default)
- Optimize partition size (~128MB per partition)

---

## 📈 Hasil dan Insights

### RFM Segmentation Results

**Segment Distribution** (contoh):
```
Champions:        15% (15,000 customers)
Loyal Customers:  30% (30,000 customers)
At Risk:          25% (25,000 customers)
New Customers:    30% (30,000 customers)
```

**Business Actions**:
- **Champions**: VIP program, exclusive offers
- **Loyal Customers**: Loyalty rewards, referral program
- **At Risk**: Win-back campaigns, special discounts
- **New Customers**: Onboarding program, first purchase incentives

---

### Churn Analysis Results

**Model Performance** (contoh):
```
Accuracy:  85%
Precision: 82%
Recall:    78%
F1-Score:  80%
```

**Top Features Influencing Churn**:
1. Recency (40%)
2. Frequency (25%)
3. Monetary (20%)
4. Country (10%)
5. RFM Segment (5%)

**Business Insights**:
- Customers with recency > 90 days have 75% churn probability
- Low frequency customers (< 3 transactions) are 3x more likely to churn
- Country-specific retention strategies needed

---

## 🎓 Kesimpulan

### Pencapaian Project

1. ✅ **Berhasil membangun pipeline ETL end-to-end**
   - Bronze layer untuk raw data storage
   - Silver layer untuk data cleaning dan integration
   - Gold layer untuk analytics dan insights

2. ✅ **Implementasi Medallion Architecture**
   - Separation of concerns
   - Data quality improvement di setiap layer
   - Scalable dan maintainable

3. ✅ **Distributed Processing dengan Spark**
   - Mampu memproses 1M+ records
   - Parallel processing untuk performance
   - Integration dengan MinIO (S3-compatible storage)

4. ✅ **Machine Learning Implementation**
   - Customer segmentation dengan K-Means
   - Churn prediction dengan Random Forest
   - Actionable business insights

---

### Teknologi yang Dipelajari

- **Docker & Docker Compose**: Containerization dan orchestration
- **Apache Spark**: Distributed data processing
- **MinIO**: Object storage (S3-compatible)
- **PostgreSQL**: Relational database
- **PySpark**: Python API untuk Spark
- **Scikit-learn**: Machine learning
- **Jupyter Notebook**: Interactive development

---

### Improvement Opportunities

1. **Automation**:
   - Implement Apache Airflow untuk workflow orchestration
   - Schedule pipeline runs (daily/weekly)

2. **Data Quality**:
   - Add data validation rules
   - Implement data quality metrics
   - Alert on data anomalies

3. **Monitoring**:
   - Add Prometheus + Grafana untuk monitoring
   - Track pipeline performance metrics
   - Set up alerting

4. **Scalability**:
   - Add more Spark workers untuk parallel processing
   - Implement dynamic resource allocation
   - Optimize partition strategy

5. **ML Model**:
   - Model versioning dengan MLflow
   - A/B testing untuk model comparison
   - Real-time prediction API

---

### Referensi

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [RFM Analysis](https://en.wikipedia.org/wiki/RFM_(market_research))
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 👥 Tim Kelompok 4

**Anggota**:
- [Nama Anggota 1] - [NIM]
- [Nama Anggota 2] - [NIM]
- [Nama Anggota 3] - [NIM]
- [Nama Anggota 4] - [NIM]

**Dosen Pengampu**: [Nama Dosen]

**Mata Kuliah**: Big Data

**Tahun Akademik**: 2025/2026

---

**Terakhir diupdate**: 23 April 2026
