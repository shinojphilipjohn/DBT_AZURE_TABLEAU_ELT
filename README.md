# DBT_AZURE_TABLEAU_ELT

An end-to-end production-grade ELT data pipeline built on Microsoft Azure, transforming the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (~100K orders, 9 relational tables) from raw CSV files to analytics-ready dimensional models.

---

## Architecture

```
Azure Blob Storage (raw CSVs)
        ↓
┌─────────────────────────────────────────┐
│            Ingestion Layer              │
│  Python Script  +  Azure Data Factory   │
└─────────────────────────────────────────┘
        ↓
Azure SQL DB — raw schema (Bronze)
        ↓
dbt Core — staging schema (Silver)
        ↓
dbt Core — mart schema (Gold)
        ↓
GitHub Actions CI/CD
(dbt run + dbt test on every push, PR, and manual trigger)
```

### Medallion Architecture

| Layer | Schema | Tool | Purpose |
|---|---|---|---|
| Bronze | `raw` | Python / ADF | Exact copy of source, source of truth |
| Silver | `dev/prod_olist_staging` | dbt staging | Clean, rename, cast, enrich |
| Gold | `dev/prod_olist_mart` | dbt mart | Kimball star schema, BI-ready |

---

## Tech Stack

| Category | Technology |
|---|---|
| Cloud | Microsoft Azure (Australia East) |
| Storage | Azure Blob Storage |
| Database | Azure SQL Database (Serverless) |
| Ingestion (code) | Python, azure-storage-blob SDK, pandas, SQLAlchemy |
| Ingestion (no-code) | Azure Data Factory |
| Transformation | dbt Core, dbt-sqlserver adapter |
| Testing | dbt schema tests, dbt_utils |
| CI/CD | GitHub Actions |
| Authentication | Microsoft Entra DefaultAzureCredential |
| Version Control | Git, GitHub |

---

## Project Structure

```
DBT_AZURE_TABLEAU_ELT/
├── .github/
│   └── workflows/
│       └── dbtest.yml          # GitHub Actions CI/CD workflow
├── ingestion/
│   ├── azure_blob_ingestion.py # Upload CSVs to Azure Blob Storage
│   └── sqldb_ingestion.py      # Python ELT: Blob → Azure SQL DB
├── olist_dbt/
│   ├── models/
│   │   ├── staging/            # Silver layer — 9 staging models
│   │   └── mart/               # Gold layer — fact + dim models
│   ├── macros/
│   │   └── generate_schema_name.sql  # Custom schema naming macro
│   ├── packages.yml            # dbt_utils dependency
│   └── dbt_project.yml         # dbt project config
├── raw_source_files/           # Original Olist CSV files
├── .gitignore
└── README.md
```

---

## Ingestion Layer

### Python Ingestion Script

The Python script (`ingestion/sqldb_ingestion.py`) reads all 9 CSV files from Azure Blob Storage and loads them as raw tables into Azure SQL DB:

- Authenticates via `DefaultAzureCredential` — no hardcoded credentials
- Connects to Azure SQL DB via SQLAlchemy with token injection through event listener pattern
- Reads CSVs using `pandas` with `latin-1` encoding to handle Portuguese special characters
- Loads into `raw` schema using `df.to_sql()` with `chunksize=1000` for performance
- Uses `if_exists="replace"` — full reload on every run preserving raw as source of truth

### Azure Data Factory Pipeline

The ADF pipeline (`BLOB-SQLDB-AUS`) provides a native Azure no-code ingestion path alongside the Python script — demonstrating both approaches:

**Pipeline Activities:**

```
Get Metadata Activity
└── Reads all files from Blob container (Child items)
        ↓
Filter Activity
└── Excludes olist_order_reviews_dataset.csv
    (multi-line text fields incompatible with ADF CSV parser)
        ↓
ForEach Activity (Sequential)
└── Iterates through each remaining CSV file
        ↓
    Script Activity
    └── DROP TABLE IF EXISTS raw.<filename>
        ↓
    Copy Data Activity
    ├── Source: Azure Blob Storage (DelimitedText, UTF-8, quote char: ")
    └── Sink: Azure SQL DB (Auto create table, raw schema)
             Table name: dynamic — @replace(item().name, '.csv', '')
```

**Authentication:**
- Blob Storage → ADF Managed Identity with `Storage Blob Data Reader` role
- Azure SQL DB → ADF Managed Identity with `db_owner` role

**Trigger:**
- Daily schedule trigger configured (disabled post-build to avoid unnecessary runs)
- Manual trigger available via Azure Portal for on-demand execution

**Monitoring:**
- Azure Monitor alert configured to send email + SMS on pipeline failure
- Pipeline run history visible in ADF Monitor tab

**Note on reviews file:** `olist_order_reviews_dataset.csv` contains review comments with embedded newlines and special characters that exceed ADF's CSV parser capabilities. This file is handled exclusively by the Python ingestion script.

---

## Data Model

### Staging Layer (Silver) — 9 Models

| Model | Description |
|---|---|
| `customer` | Customer IDs, zip codes, city, state |
| `geolocation` | Zip code to lat/lng mapping — deduplicated by most frequent city per zip |
| `orders` | Order lifecycle — status, timestamps, delivery dates |
| `order_items` | Line items per order — product, seller, price, freight |
| `order_payments` | Payment method and value per order |
| `order_reviews` | Review scores and comments per order |
| `products` | Product attributes — category, dimensions, weight (converted to metric) |
| `sellers` | Seller location data |
| `product_category_name_translation` | Brazilian → English category name mapping |

All staging models add `transformed_date` timestamp for incremental watermarking.

### Mart Layer (Gold) — Kimball Star Schema

**Fact Tables (Incremental with Upsert):**

| Model | Grain | Unique Key | Materialization |
|---|---|---|---|
| `fact_orders` | One row per order | `order_id` | Incremental |
| `fact_order_items` | One row per item per order | `order_id + item_id` | Incremental |
| `fact_order_payments` | One row per payment per order | `order_id + payment_sequential` | Incremental |
| `fact_reviews` | One row per review | `order_id + review_id` | Incremental |

**Dimension Tables (Full Reload):**

| Model | Description | Materialization |
|---|---|---|
| `dim_customers` | Customer info enriched with avg lat/lng per zip code from geolocation | Table |
| `dim_products` | Product attributes joined with English category translation | Table |
| `dim_sellers` | Seller location info | Table |

**Star Schema:**

```
              dim_customers
                    |
dim_sellers ── fact_orders ── fact_order_items ── dim_products
                    |
              fact_order_payments
                    |
              fact_reviews
```

---

## Data Quality Tests

46 automated dbt tests:

| Test Type | Coverage |
|---|---|
| `unique` | Primary keys on all fact and dim tables |
| `not_null` | All primary and foreign key columns |
| `relationships` | FK integrity between fact and dim tables |
| `dbt_utils.unique_combination_of_columns` | Composite key validation on multi-key facts |

```bash
dbt test --target dev     # dev environment
dbt test --target prod    # prod environment
```

---

## CI/CD Pipeline

GitHub Actions workflow triggers on:

| Event | Target | Action |
|---|---|---|
| Push to `main` | prod | `dbt run + dbt test` |
| Push to `test-branch` | dev | `dbt run + dbt test` |
| Pull Request to `main` | dev | `dbt run + dbt test` |
| Manual trigger | prod | `dbt run + dbt test` |

Branch protection rules on `main` require all dbt tests to pass before merging — only tested code reaches production.

---

## Running the Pipeline

```bash
# Ingest raw data to Azure SQL DB (Python)
python ingestion/sqldb_ingestion.py

# Run dbt transformations
cd olist_dbt
dbt run --target dev

# Run data quality tests
dbt test --target dev

# Deploy to production
dbt run --target prod
dbt test --target prod

# Full refresh (reset incremental tables)
dbt run --full-refresh --target prod
```

---

## Key Architectural Decisions

**ELT over ETL**
Raw data is loaded as-is into the bronze layer — all transformation logic lives in dbt. The raw layer is an immutable source of truth that can always be used to rerun transformations from scratch.

**Dual Ingestion Methods**
Two ingestion approaches demonstrate different engineering tradeoffs:
- Python script — fine-grained control, encoding handling, custom enrichment
- ADF Copy Activity — native Azure integration, Managed Identity auth, visual pipeline monitoring

**Microsoft Entra DefaultAzureCredential**
Zero hardcoded credentials throughout. Python uses token injection via SQLAlchemy event listener. ADF uses Managed Identity. GitHub Actions uses Service Principal via secrets.

**Kimball Dimensional Modelling**
Mart layer implements Kimball star schema — clearly defined grain per fact table, denormalised dimension tables for query performance, referential integrity enforced via dbt relationship tests.

**Incremental Materialisation with Upsert**
Fact tables use incremental materialisation with `unique_key` — dbt generates a MERGE statement that updates existing rows and inserts new ones. Watermark uses `transformed_date` timestamp from staging layer.

**Serverless Azure SQL**
Azure SQL Database serverless tier auto-pauses when idle — total project infrastructure cost: AU$1.01 for the entire build and test phase.

**Dev/Prod Environment Separation**
dbt profiles.yml defines separate dev and prod targets. Feature branches run against dev schemas, merges to main deploy to prod schemas — only tested code reaches production.

**Visualisation**
A Tableau dashboard layer was not built as part of this project — a separate Tableau portfolio already demonstrates BI and visualisation skills. The mart layer tables are structured and ready for direct connection to any BI tool (Tableau, Power BI, Looker).

---

## Known Data Quality Issues

**Geolocation duplicates**
8 zip codes have conflicting state assignments in source data. Pipeline takes the most frequent city/state combination per zip code using `ROW_NUMBER() OVER (PARTITION BY zip_code ORDER BY freq DESC)`.

**BOM character**
`product_category_name_translation.csv` contains a UTF-8 BOM character in the first column name — handled in staging model using SQL Server square bracket notation `[ï»¿product_category_name]`.

**Order reviews CSV**
Multi-line review comment fields with embedded newlines exceed ADF's CSV parser capability — handled exclusively by Python ingestion script with `latin-1` encoding.

---

## Data Source

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

~100,000 orders placed between 2016 and 2018 across multiple marketplaces in Brazil.

---

## Author

**Shinoj Philip John**
Melbourne, Australia
[LinkedIn](https://linkedin.com/in/shinojphilipjohn)
