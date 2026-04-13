#Downloads the dataset from Kaggle.

import os
import logging
from pathlib import Path

KAGGLE_DATASET = "adamgbor/club-football-match-data-2000-2025"
LOCAL_DOWNLOAD_DIR = Path("/tmp/football")
EXPECTED_FILENAME = "Matches.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _load_kaggle_credentials() -> None:
    from airflow.models import Variable

    os.environ["KAGGLE_USERNAME"] = Variable.get("KAGGLE_USERNAME")
    os.environ["KAGGLE_KEY"] = Variable.get("KAGGLE_KEY")

    logger.info("Kaggle credentials loaded.")

def _prepare_download_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def download_dataset() -> str:
    _load_kaggle_credentials()

    import kaggle

    _prepare_download_dir(LOCAL_DOWNLOAD_DIR)

    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        dataset=KAGGLE_DATASET,
        path=str(LOCAL_DOWNLOAD_DIR),
        unzip=True,
        quiet=False,
    )

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
