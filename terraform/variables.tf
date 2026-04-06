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
  description = "GCS bucket used as the raw data lake"
  type        = string
  default     = "eu-football-raw-20-25"
}

variable "service_account_name" {
  description = "ID of the dedicated service account for this pipeline"
  type        = string
  default     = "eu-football-pipeline-sa"
}

variable "bq_datasets" {
  description = "List of BigQuery dataset IDs to create (medallion architecture: raw → staging → mart)"
  type        = list(string)
  default     = ["eu_football_raw", "eu_football_staging", "eu_football_mart"]
}
