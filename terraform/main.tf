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

# Project APIs

resource "google_project_service" "apis" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com"
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# IAM & Service Account

resource "google_service_account" "pipeline_sa" {
  account_id   = var.service_account_name
  display_name = "EU Football Pipeline Service Account"

  depends_on = [google_project_service.apis]
}

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

# Generate JSON key for local development and Airflow Container credentials
resource "google_service_account_key" "pipeline_sa_key" {
  service_account_id = google_service_account.pipeline_sa.name
}

resource "local_file" "pipeline_sa_key_file" {
  content         = base64decode(google_service_account_key.pipeline_sa_key.private_key)
  filename        = "${path.module}/../credentials/pipeline-sa-key.json"
  file_permission = "0644"    # The airflow user inside the container needs read access (644).
}

# Cloud Storage

resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true # Allows terraform destroy even if the bucket has objects

  uniform_bucket_level_access = true

  depends_on = [google_project_service.apis]
}

# BigQuery Datasets

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
