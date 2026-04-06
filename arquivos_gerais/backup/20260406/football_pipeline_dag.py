"""
football_pipeline_dag.py — Airflow DAG for the EU Football Analytics pipeline.

Pipeline flow:
    download_csv >> upload_to_gcs >> create_external_table >> dbt_run

This DAG runs dbt Core locally inside the Composer environment using BashOperator.
No dbt Cloud account or API token is required. Authentication to BigQuery is handled
automatically via the Composer environment's attached Service Account.

Environment variables (set via Composer env_variables in Terraform):
    PIPELINE_BUCKET   : GCS bucket name
    PIPELINE_PROJECT  : GCP project ID
    PIPELINE_RAW_DS   : BigQuery raw dataset ID
    DBT_PROJECT_DIR   : Absolute path to the dbt project inside the Composer worker
                        Default: /home/airflow/gcs/dags/football_dbt
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Import pipeline scripts
from scripts.download_dataset import download_dataset
from scripts.upload_to_gcs import upload_to_gcs
from scripts.create_external_table import create_external_table

# ── Logging ───────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

# The dbt project lives under the Composer DAGs folder, which is synced from GCS.
# Cloud Composer mounts the DAGs bucket at /home/airflow/gcs/dags inside each worker.
DBT_PROJECT_DIR = os.getenv(
    "DBT_PROJECT_DIR",
    "/home/airflow/gcs/dags/football_dbt",
)

# profiles.yml is placed alongside the dbt project (see football_dbt/profiles.yml).
# Passing --profiles-dir keeps everything self-contained inside the repo.
DBT_PROFILES_DIR = DBT_PROJECT_DIR

# ── Default arguments ─────────────────────────────────────────────────────────

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="football_pipeline",
    description="End-to-end pipeline: Kaggle → GCS → BigQuery → dbt Core",
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

    # ── dbt Core tasks ────────────────────────────────────────────────────────
    # We split dbt into two tasks so failures are easier to diagnose.
    # dbt seed loads the leagues.csv reference table before the models run.

    # t4_dbt_deps = BashOperator(
    # task_id="dbt_deps",
    # bash_command=(
    # f"dbt deps "
    # f"--project-dir {DBT_PROJECT_DIR} "
    # f"--profiles-dir {DBT_PROFILES_DIR}"
    # ),
    # )

    t4_dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=(
            f"dbt seed "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--target prod "
            f"--full-refresh"  # always reload seed data so it stays in sync
        ),
    )

    t5_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"dbt run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--target prod"
        ),
    )

    t6_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"dbt test "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--target prod"
        ),
    )

    # ── Task dependencies ─────────────────────────────────────────────────────
    t1_download >> t2_upload >> t3_external_table >> t4_dbt_seed >> t5_dbt_run >> t6_dbt_test
