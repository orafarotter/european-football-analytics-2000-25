output "service_account_email" {
  description = "Pipeline service account — use this in dbt Cloud and Airflow connections"
  value       = google_service_account.pipeline_sa.email
}

output "data_lake_bucket_name" {
  description = "GCS bucket name — use this as the upload destination in the DAG"
  value       = google_storage_bucket.data_lake.name
}

output "data_lake_bucket_url" {
  description = "GCS bucket URL"
  value       = "gs://${google_storage_bucket.data_lake.name}"
}

output "bigquery_dataset_ids" {
  description = "Map of created BigQuery dataset IDs"
  value       = { for k, v in google_bigquery_dataset.datasets : k => v.dataset_id }
}

output "composer_environment_name" {
  description = "Cloud Composer environment name"
  value       = google_composer_environment.airflow.name
}

output "composer_airflow_uri" {
  description = "Airflow web UI URL"
  value       = google_composer_environment.airflow.config[0].airflow_uri
}
