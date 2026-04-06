"""
download_dataset.py — Downloads the Club Football Match Data (2000-2025) from Kaggle.

This script is called by the Airflow DAG (download_csv task).
Kaggle credentials are read from Airflow Variables to avoid storing
sensitive data in the repository.

Airflow Variables required:
    KAGGLE_USERNAME  : Kaggle account username
    KAGGLE_API_TOKEN : Kaggle API key

The kaggle library expects these specific environment variable names:
    KAGGLE_USERNAME  → set directly from the Airflow Variable
    KAGGLE_KEY       → set from the KAGGLE_API_TOKEN Airflow Variable
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
    """
    Load Kaggle credentials from Airflow Variables into environment variables.

    The kaggle library authenticates using:
        KAGGLE_USERNAME — account username
        KAGGLE_KEY      — API token (note: the env var name is KAGGLE_KEY,
                          not KAGGLE_API_TOKEN; the Airflow Variable is stored
                          as KAGGLE_API_TOKEN for clarity but mapped here)
    """
    from airflow.models import Variable

    os.environ["KAGGLE_USERNAME"] = Variable.get("KAGGLE_USERNAME")
    # The kaggle library expects KAGGLE_KEY specifically — not KAGGLE_API_TOKEN
    os.environ["KAGGLE_KEY"] = Variable.get("KAGGLE_API_TOKEN")

    logger.info("Kaggle credentials loaded from Airflow Variables.")


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
        FileNotFoundError: If the expected CSV file is not found after download.
    """
    _load_kaggle_credentials()

    import kaggle

    _prepare_download_dir(LOCAL_DOWNLOAD_DIR)

    logger.info("Starting download of dataset: %s", KAGGLE_DATASET)

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

    csv_path = LOCAL_DOWNLOAD_DIR / EXPECTED_FILENAME
    if not csv_path.exists():
        downloaded = list(LOCAL_DOWNLOAD_DIR.iterdir())
        raise FileNotFoundError(
            f"Expected file '{EXPECTED_FILENAME}' not found in {LOCAL_DOWNLOAD_DIR}. "
            f"Files present: {[f.name for f in downloaded]}"
        )

    logger.info("Dataset downloaded successfully: %s", csv_path)
    return str(csv_path)
