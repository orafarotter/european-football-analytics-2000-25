# ============================================================
# variables.tf — Input variables for the European Football pipeline
# ============================================================

variable "project_id" {
  description = "GCP project ID where all resources will be created"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "GCP zone (used by Composer)"
  type        = string
  default     = "us-east1-b"
}

variable "bucket_name" {
  description = "GCS bucket used as data lake"
  type        = string
  default     = "eu-football-raw-20-25"
}

variable "service_account_name" {
  description = "Dedicated service account for this pipeline"
  type        = string
  default     = "eu-football-pipeline-sa"
}

variable "composer_env_name" {
  description = "Cloud Composer (Airflow) environment"
  type        = string
  default     = "eu-football-composer-env"
}

variable "composer_image_version" {
  description = "Composer image version (Airflow 2.x on Composer 2)"
  type        = string
  default     = "composer-2.6.6-airflow-2.7.3"
}

variable "bq_datasets" {
  description = "List of BigQuery dataset IDs to create (medallion layers)"
  type        = list(string)
  default     = ["eu_football_raw", "eu_football_staging", "eu_football_mart"]
}