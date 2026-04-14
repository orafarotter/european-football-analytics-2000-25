# European Football Analytics 2000–2025 🇪🇺🏟️

An end-to-end **batch ELT data pipeline** built on Google Cloud Platform (GCP), using a single public Kaggle dataset to answer analytical questions about the top 10 European football leagues — from raw data to an interactive Looker Studio dashboard.

> 📊 **[View the Live Dashboard](https://lookerstudio.google.com/reporting/67b7d22f-b31f-40de-9af0-f8a87ab10c17)**

---

## 📌 Problem Description

The dataset contains football match data from more than 30 leagues worldwide, spanning from the 2000/01 season through the most recent results of the 2024/25 season.

This project focuses on the **top 10 European leagues**, selected based on the [Opta Power Rankings (Apr 2, 2026)](https://theanalyst.com/articles/strongest-football-leagues-in-the-world-opta-power-rankings), and answers the following analytical questions:

- 🏆 Which leagues have the most matches played?
- ⚽ How has the average number of goals per match evolved over time?
- 📊 How are match results distributed (Home Win / Away Win / Draw)?
- 🔥 Which leagues produce the most high-scoring, intense matches?

> **Note:** Only the main CSV file from the dataset is used in this project.

---

## 🗺️ Architecture

```
[Kaggle API]
     │
     ▼  Python (Airflow DAG)
[Cloud Storage — GCS: raw/matches.csv]
     │
     ▼  BigQuery External Table (Airflow DAG)
[BigQuery — eu_football_raw]         ← Bronze: raw external table
     │
     ▼  dbt (triggered via Airflow DAG)
[BigQuery — eu_football_staging]     ← Silver: cleaned, typed, deduplicated views
     │
     ▼
[BigQuery — eu_football_mart]        ← Gold: partitioned + clustered fact table
     │
     ▼
[Looker Studio — Dashboard]
```

This project follows the **Medallion / ELT** pattern:
- **Bronze** — raw data landed in GCS and exposed via BigQuery external table
- **Silver** — staging layer: type casting, deduplication, join with league metadata (dbt seed)
- **Gold** — mart layer: filtered, enriched, partitioned by year, clustered by league

---

## 🏗️ Tech Stack

| Layer                         | Technology                        |
|-------------------------------|-----------------------------------|
| Cloud                         | Google Cloud Platform (GCP)       |
| Infrastructure as code (IaC)  | Terraform                         |
| Workflow orchestration        | Apache Airflow (Docker)           |
| Data Lake                     | Google Cloud Storage (GCS)        |
| Data Warehouse                | BigQuery                          |
| Transformations               | dbt Core                          |
| Dashboard                     | Looker Studio                     |

---

## 📦 Dataset

- **Source:** [Club Football Match Data 2000–2025 — Kaggle](https://www.kaggle.com/datasets/adamgbor/club-football-match-data-2000-2025)
- **Format:** Single CSV file
- **Coverage:** 30+ leagues worldwide, seasons 2000/01 through 2024/25
- **Used in this project:** 10 European leagues (see below)

### Leagues Selected

| Code | Country  | League            |
|------|----------|-------------------|
| E0   | England  | Premier League    |
| SP1  | Spain    | La Liga           |
| D1   | Germany  | Bundesliga        |
| I1   | Italy    | Serie A           |
| F1   | France   | Ligue 1           |
| B1   | Belgium  | Pro League        |
| P1   | Portugal | Primeira Liga     |
| E1   | England  | Championship      |
| DEN  | Denmark  | Superliga         |
| POL  | Poland   | Ekstraklasa       |

---

## 📁 Repository Structure

```
european-football-analytics-2000-25/
├── terraform/               # GCP infrastructure (IaC)
├── dags/                    # Airflow DAG
├── dbt/                     # dbt project (models, seeds, tests)
├── .env.example             # Environment variable template
├── .gitignore
├── docker-compose.yaml
├── Dockerfile
├── README.md
├── requirements.txt
└── setup.sh                 # Sets Airflow Variables from .env
```

---

## 🚀 How to Reproduce

> ⚠️ The commands below were tested in a **WSL Ubuntu** environment. Any Linux terminal should work equivalently.

### Prerequisites

Before you begin, make sure you have the following installed and configured:

1. **Google Cloud account** with billing enabled and a project created
   → https://cloud.google.com/

2. **Google Cloud SDK** installed and configured
   → https://cloud.google.com/sdk/docs/install

3. **Terraform** installed
   → https://developer.hashicorp.com/terraform/install

4. **Docker** (with Docker Compose) installed
   → https://docs.docker.com/engine/install/

5. **Kaggle account** (to generate an API key)
   → https://www.kaggle.com/

---

### Step 1 — Clone the Repository & Configure Environment Variables

```bash
git clone https://github.com/orafarotter/european-football-analytics-2000-25.git
cd european-football-analytics-2000-25
```

Copy the environment variable template and fill in your values:

```bash
mv .env.example .env
```

Edit `.env` with your values:

| Variable | Description | How to get it |
|---|---|---|
| `AIRFLOW_SECRET_KEY` | Random secret for Airflow web server | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `AIRFLOW__CORE__FERNET_KEY` | Encryption key for Airflow connections | Run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GCP_PROJECT_ID` | Your GCP Project ID | GCP Console → Project selector |
| `GCP_REGION` | GCP region (e.g. `us-east1`) | Your preferred region |
| `GCS_BUCKET` | Name for the GCS bucket | Choose a globally unique name |
| `KAGGLE_USERNAME` | Your Kaggle username | kaggle.com → Settings → Active logins |
| `KAGGLE_KEY` | Your Kaggle API key | kaggle.com → Settings → API Tokens → Generate New Token |

---

### Step 2 — Configure Terraform Variables

```bash
cd terraform
mv terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id           = "<GCP_PROJECT_ID>"
region               = "<REGION>"
bucket_name          = "<BUCKET_NAME>"
service_account_name = "<SERVICE_ACCOUNT_NAME>"
```

> ⚠️ `project_id`, `region`, and `bucket_name` must match the values set in `.env`.
> The `service_account_name` must match the regex: `^[a-z]([-a-z0-9]*[a-z0-9])?$`

---

### Step 3 — Authenticate with GCP & Provision Infrastructure

Authenticate with your Google account:

```bash
gcloud auth login
```

If you have multiple projects, confirm you are using the correct one:

```bash
gcloud config get-value project
# If incorrect:
gcloud config set project <GCP_PROJECT_ID>
```

Then provision the infrastructure with Terraform (still inside the `terraform/` folder):

```bash
terraform init
terraform plan
terraform apply
```

Wait for the provisioning to complete. This will create:
- A dedicated GCP Service Account with least-privilege roles
- A GCS bucket for the raw data lake
- BigQuery datasets: `eu_football_raw`, `eu_football_staging`, `eu_football_mart`

---

### Step 4 — Start Airflow and Run the Pipeline

Return to the project root:

```bash
cd ..
```

Build the Docker image and initialize Airflow:

```bash
docker compose build          # Build the custom image (uses cache on subsequent runs)
docker compose up airflow-init  # Runs DB migrations and creates the admin user
docker compose up -d            # Start all containers in detached mode
bash setup.sh                   # Inject Airflow Variables from your .env file
```

Access the Airflow UI at **http://localhost:8080**

```
Username: admin
Password: admin
```

The DAG will appear on the home screen. Enable it using the **toggle switch**, then open it to monitor execution.

#### What the pipeline does

The DAG runs the following tasks in sequence:

1. **`download_csv`** — Downloads the raw CSV from Kaggle using your API credentials and saves it locally inside the container.
2. **`upload_to_gcs`** — Uploads `matches.csv` to the GCS bucket under `raw/matches.csv`. Existing files are overwritten (idempotent).
3. **`create_external_table`** — Creates (or replaces) a BigQuery external table in `eu_football_raw` pointing to the GCS file, with an explicit schema.
4. **`run_dbt`** — Runs the full dbt project:
   - Seeds the `leagues` reference table
   - Builds `stg_matches` (view): type casting, deduplication, join with league metadata
   - Builds `fct_european_matches` (table): filtered for the 10 European leagues, partitioned by year, clustered by league and league name, with enriched columns (`total_goals`, `goal_difference`, `match_result_label`, `scoring_category`)
   - Runs 21 dbt tests (not_null, accepted_values, relationships)

Once the DAG completes successfully, verify the output in **BigQuery** → `eu_football_mart` → `fct_european_matches`.

---

### Step 5 — Explore the Dashboard

A pre-built dashboard is available here:

> 📊 **[European Football Analytics — Looker Studio](https://lookerstudio.google.com/reporting/67b7d22f-b31f-40de-9af0-f8a87ab10c17)**

To build your own dashboard connected to your data:

1. Go to [https://lookerstudio.google.com](https://lookerstudio.google.com)
2. Click **+ Create** → **Report**
3. Connect to **BigQuery**:
   - Project: your GCP project
   - Dataset: `eu_football_mart`
   - Table: `fct_european_matches`
4. If prompted with *"You are about to add data to this Report"*, click **Add to Report**

You are now ready to build your own visualizations.

---

### Teardown

To stop and remove all containers:

```bash
docker compose down
```

To destroy all GCP infrastructure provisioned by Terraform:

```bash
cd terraform
terraform destroy
```

---

## 📊 Dashboard Preview

![Dashboard Screenshot](assets/dashboard_screenshot.png)

> **[Open Dashboard](https://lookerstudio.google.com/reporting/67b7d22f-b31f-40de-9af0-f8a87ab10c17)**
>
> *Covering the 10 strongest European leagues based on Opta Power Rankings (Apr 2, 2026)*

**Tiles:**
- 🔢 KPI Scorecards — Total Matches · Average Goals per Match
- 📈 Line Chart — Average Goals per Match by Year (2000–2025)
- 📊 Bar Chart — Total Matches by League
- 🍩 Donut Chart — Match Result Distribution (Home Win / Away Win / Draw)
- 📊 Stacked Bar Chart — Match Intensity by League (`scoring_category`)

---

## ⭐ Going the Extra Mile

- **dbt tests** — 21 tests across all models covering `not_null`, `accepted_values`, and `relationships` constraints. All tests pass ✅
- **Partitioning & Clustering** — `fct_european_matches` is partitioned by year (`DATE_TRUNC(match_date, YEAR)`) and clustered by `division` and `league_name` for optimal query performance and cost efficiency in BigQuery
- **Idempotent pipeline** — every step can be re-run safely; GCS upload overwrites the existing file and the external table is created with `CREATE OR REPLACE`
- **Least-privilege IAM** — the service account provisioned by Terraform has only the minimum roles required (`storage.admin`, `bigquery.admin`)

---

## 🔐 Security Notes

- Never commit credentials or service account keys to the repository
- `.gitignore` excludes `*.json`, `*.tfvars`, and `.env`
- Use `terraform.tfvars.example` and `.env.example` as safe templates for collaborators
- Airflow credentials are injected via Variables (no hardcoding in DAG files)