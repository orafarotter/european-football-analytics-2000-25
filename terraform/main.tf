terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.25.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ===========================
# REQUIRED APIS
# ===========================
# Only the APIs actually used by this pipeline are enabled.
# Composer was removed — orchestration now runs locally via Docker Compose.

resource "google_project_service" "apis" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com"
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ===========================
# SERVICE ACCOUNT
# ===========================

resource "google_service_account" "pipeline_sa" {
  account_id   = var.service_account_name
  display_name = "EU Football Pipeline Service Account"

  depends_on = [google_project_service.apis]
}

# Principle of least privilege: only the roles required for this pipeline.
# - storage.admin   : read/write to the GCS data lake bucket
# - bigquery.admin  : create datasets, external tables and run dbt models
locals {
  sa_roles = [
    "roles/storage.admin",
    "roles/bigquery.admin",
  ]
}

resource "google_project_iam_member" "pipeline_sa_roles" {
  for_each = toset(local.sa_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Generate a JSON key for the service account.
# This key is used by the Airflow Docker container via GOOGLE_APPLICATION_CREDENTIALS.
# The key file is written locally and must NEVER be committed to the repository.
resource "google_service_account_key" "pipeline_sa_key" {
  service_account_id = google_service_account.pipeline_sa.name
}

resource "local_file" "pipeline_sa_key_file" {
  content         = base64decode(google_service_account_key.pipeline_sa_key.private_key)
  filename        = "${path.module}/../credentials/pipeline-sa-key.json"
  file_permission = "0600" # owner read/write only
}

# ===========================
# CLOUD STORAGE
# ===========================

resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true # allows terraform destroy even if the bucket has objects

  uniform_bucket_level_access = true # enforces IAM-only access (no ACLs)

  depends_on = [google_project_service.apis]
}

# ===========================
# BIGQUERY DATASETS
# ===========================
# Three datasets following the medallion architecture:
#   eu_football_raw      → external table over raw GCS CSV (Bronze)
#   eu_football_staging  → cleaned and typed models (Silver)
#   eu_football_mart     → partitioned and clustered analytical models (Gold)

resource "google_bigquery_dataset" "datasets" {
  for_each = toset(var.bq_datasets)

  dataset_id                 = each.value
  location                   = var.region
  delete_contents_on_destroy = true

  labels = {
    project     = "eu-football-analytics"
    environment = "production"
  }

  depends_on = [google_project_service.apis]
}
