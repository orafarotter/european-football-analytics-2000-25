#!/bin/bash
set -e

# Load .env
export $(grep -v '^#' .env | xargs)

echo "▶ Generating terraform.tfvars..."
cat > terraform/terraform.tfvars <<EOF
project_id = "${GCP_PROJECT_ID}"
region     = "${GCP_REGION}"
bucket     = "${GCS_BUCKET}"
EOF

echo "▶ Setting Airflow Variables..."
docker compose exec airflow-scheduler airflow variables set KAGGLE_USERNAME "${KAGGLE_USERNAME}"
docker compose exec airflow-scheduler airflow variables set KAGGLE_KEY "${KAGGLE_KEY}"
docker compose exec airflow-scheduler airflow variables set GCP_PROJECT_ID "${GCP_PROJECT_ID}"
docker compose exec airflow-scheduler airflow variables set GCS_BUCKET "${GCS_BUCKET}"

echo "▶ Setting Airflow GCP Connection..."
docker compose exec airflow-scheduler airflow connections add google_cloud_default \
    --conn-type google_cloud_platform \
    --conn-extra '{"key_path": "/opt/airflow/credentials/pipeline-sa-key.json", "scope": "https://www.googleapis.com/auth/cloud-platform", "project": "'"${GCP_PROJECT_ID}"'"}'

echo "▶ Fixing credentials file permissions..."
# The Terraform-generated key file defaults to 600 (owner-only).
# The airflow user inside the container needs read access (644).
# This is safe because the file is mounted read-only (:ro) in docker-compose.yml.
chmod 644 credentials/pipeline-sa-key.json

echo "✅ Complete setup."