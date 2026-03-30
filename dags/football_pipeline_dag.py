"""
football_pipeline_dag.py — Airflow DAG for the EU Football Analytics pipeline.

Pipeline flow:
    download_csv >> upload_to_gcs >> create_external_table >> trigger_dbt_job

Environment variables (set via Composer env_variables in Terraform):
    PIPELINE_BUCKET   : GCS bucket name
    PIPELINE_PROJECT  : GCP project ID
    PIPELINE_RAW_DS   : BigQuery raw dataset ID

Airflow Variables (set manually in the Airflow UI or via gcloud):
    DBT_ACCOUNT_ID    : dbt Cloud account ID
    DBT_JOB_ID        : dbt Cloud job ID to trigger
    DBT_API_TOKEN     : dbt Cloud API token
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

# Import pipeline scripts
from download_dataset import download_dataset
from upload_to_gcs import upload_to_gcs
from create_external_table import create_external_table

# ── Logging ───────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Default arguments ─────────────────────────────────────────────────────────

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

# ── dbt Cloud trigger ─────────────────────────────────────────────────────────


def trigger_dbt_job() -> None:
    """
    Trigger a dbt Cloud job via the dbt Cloud API v2 and wait for completion.

    Reads DBT_ACCOUNT_ID, DBT_JOB_ID, and DBT_API_TOKEN from Airflow Variables.

    Raises:
        RuntimeError: If the dbt job fails or times out.
    """
    account_id = Variable.get("DBT_ACCOUNT_ID")
    job_id = Variable.get("DBT_JOB_ID")
    api_token = Variable.get("DBT_API_TOKEN")

    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json",
    }

    # Trigger the job
    trigger_url = (
        f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs/{job_id}/run/"
    )
    trigger_payload = {"cause": "Triggered by Airflow DAG: football_pipeline"}

    logger.info("Triggering dbt Cloud job %s ...", job_id)
    response = requests.post(
        trigger_url, headers=headers, json=trigger_payload)
    response.raise_for_status()

    run_id = response.json()["data"]["id"]
    logger.info("dbt Cloud run started. Run ID: %s", run_id)

    # Poll for completion (max 30 minutes, check every 30 seconds)
    status_url = (
        f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/runs/{run_id}/"
    )
    max_attempts = 60
    poll_interval_seconds = 30

    for attempt in range(max_attempts):
        time.sleep(poll_interval_seconds)
        status_response = requests.get(status_url, headers=headers)
        status_response.raise_for_status()

        run_data = status_response.json()["data"]
        status = run_data["status"]
        status_humanized = run_data.get("status_humanized", status)

        logger.info(
            "Attempt %d/%d — dbt run status: %s",
            attempt + 1,
            max_attempts,
            status_humanized,
        )

        # dbt Cloud status codes: 1=Queued, 2=Starting, 3=Running, 10=Success, 20=Error, 30=Cancelled
        if status == 10:
            logger.info("dbt Cloud job completed successfully.")
            return
        elif status in (20, 30):
            raise RuntimeError(
                f"dbt Cloud job failed with status '{status_humanized}'. "
                f"Check the dbt Cloud UI for run ID {run_id}."
            )

    raise RuntimeError(
        f"dbt Cloud job timed out after {max_attempts * poll_interval_seconds / 60:.0f} minutes."
    )


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="football_pipeline",
    description="End-to-end pipeline: Kaggle → GCS → BigQuery → dbt Cloud",
    schedule_interval="@weekly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["football", "etl", "dbt"],
) as dag:

    t1_download = PythonOperator(
        task_id="download_csv",
        python_callable=download_dataset,
    )

    t2_upload = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=upload_to_gcs,
    )

    t3_external_table = PythonOperator(
        task_id="create_external_table",
        python_callable=create_external_table,
    )

    t4_dbt = PythonOperator(
        task_id="trigger_dbt_job",
        python_callable=trigger_dbt_job,
    )

    t1_download >> t2_upload >> t3_external_table >> t4_dbt
