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
  description = "GCS bucket for the data lake"
  type        = string
  default     = "eu-football-raw-20-25"
}

variable "service_account_name" {
  description = "Service account ID for the data pipeline"
  type        = string
  default     = "eu-football-pipeline-sa"
}

variable "bq_datasets" {
  description = "List of BigQuery datasets to create"
  type        = list(string)
  default     = ["eu_football_raw", "eu_football_staging", "eu_football_mart"]
}
