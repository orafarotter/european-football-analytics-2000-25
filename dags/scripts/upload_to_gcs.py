#Uploads the local Matches.csv to Google Cloud Storage.

import os
import logging
from pathlib import Path

BUCKET_NAME = os.environ.get("GCS_BUCKET", "eu-football-raw-20-25")
LOCAL_FILE_PATH = Path("/tmp/football/Matches.csv")
GCS_OBJECT_NAME = "raw/Matches.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def upload_to_gcs(
    local_path: Path = LOCAL_FILE_PATH,
    bucket_name: str = BUCKET_NAME,
    gcs_object_name: str = GCS_OBJECT_NAME,
) -> str:
    if not local_path.exists():
        raise FileNotFoundError(
            f"Local file not found: {local_path}."
        )

    from airflow.providers.google.cloud.hooks.gcs import GCSHook
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