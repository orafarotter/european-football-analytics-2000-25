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

resource "google_project_service" "apis" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "composer.googleapis.com",
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
}

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

# ===========================
# CLOUD STORAGE 
# ===========================

resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true 

  uniform_bucket_level_access = true   
}

# ===========================
# BIGQUERY DATASETS 
# ===========================

resource "google_bigquery_dataset" "datasets" {
  for_each = toset(var.bq_datasets)

  dataset_id                 = each.value
  location                   = var.region
  delete_contents_on_destroy = true 

  labels = {
    project     = "eu-football-analytics"
    environment = "production"
  }
}

# ===========================
# CLOUD COMPOSER ENVIRONMENT 
# ===========================

resource "google_composer_environment" "airflow" {
  name   = var.composer_env_name
  region = var.region

  config {
    software_config {
      image_version = var.composer_image_version

      pypi_packages = {
        "apache-airflow-providers-google" = "==19.0.0"
        "dbt-bigquery"                    = "==1.11.0"
        "dbt-core"                        = "==1.8.9"        
        "kaggle"                          = "==2.0.0"       
      }

      env_variables = {
        PIPELINE_BUCKET = var.bucket_name
        PIPELINE_PROJECT = var.project_id
        PIPELINE_RAW_DS  = "eu_football_raw"
        PIPELINE_STG_DS  = "eu_football_staging"
        PIPELINE_MART_DS = "eu_football_mart"
      }
    }

    workloads_config {
      scheduler {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
        count      = 1
      }
      web_server {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
      }
      worker {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
        min_count  = 1
        max_count  = 3
      }
    }

    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      service_account = google_service_account.pipeline_sa.email
    }
  }

  depends_on = [
    google_project_service.apis,
    google_project_iam_member.pipeline_sa_roles,
    google_storage_bucket.data_lake    
  ]
}
