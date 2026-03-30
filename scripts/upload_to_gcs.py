"""
upload_to_gcs.py — Uploads the local Matches.csv to Google Cloud Storage.

This script is called by the Airflow DAG (upload_to_gcs task).
Authentication is handled via Application Default Credentials (ADC):
  - In Composer: automatic via the pipeline service account.
  - Locally: run `gcloud auth application-default login` beforehand.
"""

import os
import logging
from pathlib import Path
from airflow.providers.google.cloud.hooks.gcs import GCSHook

# ── Constants ─────────────────────────────────────────────────────────────────

BUCKET_NAME = os.environ.get("PIPELINE_BUCKET", "eu-football-raw-20-25")
LOCAL_FILE_PATH = Path("/tmp/football/Matches.csv")
GCS_OBJECT_NAME = "raw/Matches.csv"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── Main ──────────────────────────────────────────────────────────────────────

def upload_to_gcs(
    local_path: Path = LOCAL_FILE_PATH,
    bucket_name: str = BUCKET_NAME,
    gcs_object_name: str = GCS_OBJECT_NAME,
) -> str:
    """
    Upload a local file to GCS, overwriting if it already exists.

    Args:
        local_path: Path to the local file to upload.
        bucket_name: Target GCS bucket name.
        gcs_object_name: Destination object name inside the bucket.

    Returns:
        str: Full GCS URI of the uploaded file (gs://...).

    Raises:
        FileNotFoundError: If the local file does not exist.
    """
    if not local_path.exists():
        raise FileNotFoundError(
            f"Local file not found: {local_path}. "
            "Make sure download_dataset.py ran successfully before this step."
        )

    hook = GCSHook()

    logger.info(
        "Uploading '%s' to gs://%s/%s ...",
        local_path,
        bucket_name,
        gcs_object_name,
    )

    hook.upload(
        bucket_name=bucket_name,
        object_name=gcs_object_name,
        filename=str(local_path),
        mime_type='text/csv'
    )

    gcs_uri = f"gs://{bucket_name}/{gcs_object_name}"
    logger.info("Upload complete: %s", gcs_uri)

    return gcs_uri
