"""
football_pipeline_dag.py — Airflow DAG for the EU Football Analytics pipeline.

Pipeline flow:
    download_csv >> upload_to_gcs >> create_external_table >> run_dbt

Authentication to GCP is handled via Application Default Credentials (ADC),
mounted into the container via the GOOGLE_APPLICATION_CREDENTIALS env variable.

Airflow Variables required (set via UI or environment):
    KAGGLE_USERNAME   : Kaggle account username
    KAGGLE_KEY        : Kaggle API key

Environment variables (set in docker-compose.yml or .env):
    GCS_BUCKET   : GCS bucket name
    GCP_PROJECT_ID  : GCP project ID
    BQ_RAW_DATASET   : BigQuery raw dataset ID
    DBT_PROJECT_DIR   : Absolute path to the dbt project inside the container
                        Default: /opt/airflow/football_dbt
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Import pipeline task functions
# These modules are importable because Airflow automatically adds the
# dags folder (/opt/airflow/dags) to sys.path.
from scripts.download_dataset import download_dataset
from scripts.upload_to_gcs import upload_to_gcs
from scripts.create_external_table import create_external_table

# ── Logging ───────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/football_dbt")
DBT_BIN = "/home/airflow/.local/bin/dbt"

# ── Default arguments ─────────────────────────────────────────────────────────

default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": lambda context: logger.error(
        "Task failed: %s", context.get("task_instance_key_str")
    ),
}

# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="football_pipeline",
    default_args=default_args,
    description="End-to-end pipeline: Kaggle → GCS → BigQuery (external table) → dbt",
    schedule="@weekly",  # 'schedule_interval' is deprecated in Airflow 2.4+
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["football", "etl", "ingestion", "dbt"],
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

    t4_dbt_run = BashOperator(
        task_id="run_dbt",
        append_env=True,
        bash_command=(
            # 1. Clear any previous tmp folder to avoid conflicts
            "rm -rf /tmp/dbt_project && "
            # 2. Copy the entire dbt project to the writable /tmp directory
            "cp -R {{ params.dbt_dir }} /tmp/dbt_project && "
            # 3. Execute all dbt commands pointing to the new /tmp location
            "{{ params.dbt_bin }} deps  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} seed  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} run   --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} test  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            # 4. Clean up after successful execution
            "rm -rf /tmp/dbt_project"
        ),
        params={
            "dbt_dir": DBT_PROJECT_DIR,
            "dbt_bin": DBT_BIN,
        },
    )

    # ── Task dependencies ─────────────────────────────────────────────────────
    t1_download >> t2_upload >> t3_external_table >> t4_dbt_run
