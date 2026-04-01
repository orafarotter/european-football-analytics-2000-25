"""
download_dataset.py — Downloads the Club Football Match Data (2000-2025) from Kaggle.

This script is called by the Airflow DAG (download_csv task).
Kaggle credentials are read from environment variables to avoid
storing sensitive files in the repository or the Composer environment.

Usage (local):
    export KAGGLE_USERNAME=your_username
    export KAGGLE_API_TOKEN=your_api_key
"""

import os
import logging
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

KAGGLE_DATASET = "adamgbor/club-football-match-data-2000-2025"
LOCAL_DOWNLOAD_DIR = Path("/tmp/football")
EXPECTED_FILENAME = "Matches.csv"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_kaggle_credentials() -> None:
    from airflow.models import Variable
    os.environ["KAGGLE_USERNAME"] = Variable.get("KAGGLE_USERNAME")
    os.environ["KAGGLE_KEY"] = Variable.get("KAGGLE_API_TOKEN")


def _prepare_download_dir(path: Path) -> None:
    """Create the local download directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    logger.info("Download directory ready: %s", path)


# ── Main ──────────────────────────────────────────────────────────────────────

def download_dataset() -> str:
    """
    Download the Kaggle dataset and return the local CSV file path.

    Returns:
        str: Absolute path to the downloaded CSV file.

    Raises:
        EnvironmentError: If Kaggle credentials are missing.
        FileNotFoundError: If the expected CSV file is not found after download.
    """
    _load_kaggle_credentials()

    import kaggle

    _prepare_download_dir(LOCAL_DOWNLOAD_DIR)

    logger.info("Starting download of dataset: %s", KAGGLE_DATASET)

    # kaggle.api authenticates automatically from KAGGLE_USERNAME / KAGGLE_API_TOKEN env vars
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        dataset=KAGGLE_DATASET,
        path=str(LOCAL_DOWNLOAD_DIR),
        unzip=True,
        quiet=False,
    )

    # Remove files that are not needed for this pipeline
    for unwanted in LOCAL_DOWNLOAD_DIR.iterdir():
        if unwanted.name != EXPECTED_FILENAME:
            unwanted.unlink()
            logger.info("Removed unwanted file: %s", unwanted.name)

    # Locate the downloaded CSV
    csv_path = LOCAL_DOWNLOAD_DIR / EXPECTED_FILENAME
    if not csv_path.exists():
        # List what was actually downloaded to help diagnose naming changes
        downloaded = list(LOCAL_DOWNLOAD_DIR.iterdir())
        raise FileNotFoundError(
            f"Expected file '{EXPECTED_FILENAME}' not found in {LOCAL_DOWNLOAD_DIR}. "
            f"Files present: {[f.name for f in downloaded]}"
        )

    logger.info("Dataset downloaded successfully: %s", csv_path)
    return str(csv_path)
