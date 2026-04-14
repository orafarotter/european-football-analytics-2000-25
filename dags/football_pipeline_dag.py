#Airflow DAG for the EU Football Analytics pipeline.

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from scripts.download_dataset import download_dataset
from scripts.upload_to_gcs import upload_to_gcs
from scripts.create_external_table import create_external_table

logger = logging.getLogger(__name__)

DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt")
DBT_BIN = "/home/airflow/.local/bin/dbt"

default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": lambda context: logger.error(
        "Task failed: %s", context.get("task_instance_key_str")
    ),
}


with DAG(
    dag_id="eu_football_pipeline",
    default_args=default_args,
    description="End-to-end pipeline: Kaggle → GCS → BigQuery → dbt",
    schedule="@weekly", 
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["elt", "ingestion", "dbt", "de_zoomcamp_26"],
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
            # Clear any previous tmp folder to avoid conflicts
            "rm -rf /tmp/dbt_project && "
            # Copy the entire dbt project to the writable /tmp directory
            "cp -R {{ params.dbt_dir }} /tmp/dbt_project && "
            # Execute all dbt commands pointing to the new /tmp location
            "{{ params.dbt_bin }} deps  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} seed  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} run   --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            "{{ params.dbt_bin }} test  --project-dir /tmp/dbt_project --profiles-dir /tmp/dbt_project && "
            # Clean up after successful execution
            "rm -rf /tmp/dbt_project"
        ),
        params={
            "dbt_dir": DBT_PROJECT_DIR,
            "dbt_bin": DBT_BIN,
        },
    )

    t1_download >> t2_upload >> t3_external_table >> t4_dbt_run
