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

# ============================================================
# 1. SERVICE ACCOUNT
# ============================================================

resource "google_service_account" "pipeline_sa" {
  account_id   = var.service_account_name
  display_name = "EU Football Pipeline Service Account"
  description  = "Dedicated SA for the EU Football Analytics pipeline (least privilege)"
}

# Assign only the roles this pipeline needs
locals {
  sa_roles = [
    "roles/storage.admin",
    "roles/bigquery.admin",
    "roles/composer.worker",
  ]
}

resource "google_project_iam_member" "pipeline_sa_roles" {
  for_each = toset(local.sa_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# ============================================================
# 2. CLOUD STORAGE — Data Lake bucket
# ============================================================

resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false # safety: prevent accidental deletion with data inside

  uniform_bucket_level_access = true # disable per-object ACLs (security best practice)

  versioning {
    enabled = false # raw CSV is always overwritten; versioning not needed here
  }

  lifecycle_rule {
    condition {
      age = 90 # move objects older than 90 days to Nearline to save costs
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# ============================================================
# 3. BIGQUERY DATASETS — Medallion layers (raw, staging, mart)
# ============================================================

resource "google_bigquery_dataset" "datasets" {
  for_each = toset(var.bq_datasets)

  dataset_id                 = each.value
  location                   = var.region
  delete_contents_on_destroy = false # safety: prevent accidental data loss

  labels = {
    project     = "eu-football-analytics"
    environment = "production"
  }
}

# ============================================================
# 4. CLOUD COMPOSER ENVIRONMENT (Managed Airflow)
# ============================================================

resource "google_composer_environment" "airflow" {
  name   = var.composer_env_name
  region = var.region

  config {
    software_config {
      image_version = var.composer_image_version

      # Python packages available to all DAGs
      pypi_packages = {
        "kaggle"             = ">=1.6"
        "apache-airflow-providers-google" = ">=10.0"
      }

      env_variables = {
        GCS_BUCKET   = var.bucket_name
        BQ_PROJECT   = var.project_id
        BQ_RAW_DS    = "eu_football_raw"
        BQ_STG_DS    = "eu_football_staging"
        BQ_MART_DS   = "eu_football_mart"
      }
    }

    node_config {
      service_account = google_service_account.pipeline_sa.email
    }
  }

  depends_on = [
    google_project_iam_member.pipeline_sa_roles,
    google_storage_bucket.data_lake,
  ]
}
