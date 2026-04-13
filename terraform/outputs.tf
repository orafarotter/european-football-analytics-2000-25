output "service_account_email" {
  description = "Pipeline service account email — useful for auditing IAM roles or identity checks"
  value       = google_service_account.pipeline_sa.email
}

output "data_lake_bucket_name" {
  description = "GCS bucket name — use this as the upload destination in the DAG"
  value       = google_storage_bucket.data_lake.name
}

output "data_lake_bucket_url" {
  description = "Full GCS URI of the data lake bucket"
  value       = "gs://${google_storage_bucket.data_lake.name}"
}

output "service_account_key_path" {
  description = "Local host path to the generated JSON key (Note: Docker containers will use their internal mapped path like /opt/airflow/...)"
  value       = local_file.pipeline_sa_key_file.filename
  sensitive   = true
}

output "bigquery_dataset_ids" {
  description = "Map of created BigQuery dataset IDs"
  value       = { for k, v in google_bigquery_dataset.datasets : k => v.dataset_id }
}
