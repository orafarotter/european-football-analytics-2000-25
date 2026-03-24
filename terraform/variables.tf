variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-east1"
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
  description = "Cloud Composer environment"
  type        = string
  default     = "eu-football-composer-env"
}

variable "composer_image_version" {
  description = "Composer image version"
  type        = string
  default     = "airflow-2.10.5-build.27"
}

variable "bq_datasets" {
  description = "List of BigQuery dataset IDs to create (medallion architecture)"
  type        = list(string)
  default     = ["eu_football_raw", "eu_football_staging", "eu_football_mart"]
}