"""
create_external_table.py — Creates (or recreates) a BigQuery external table
pointing to the raw Matches.csv file in GCS.

This script is called by the Airflow DAG (create_external_table task).
Authentication is handled via Application Default Credentials (ADC).

Usage (local):
    python scripts/create_external_table.py
"""

import os
import logging
from google.cloud import bigquery

# ── Constants ─────────────────────────────────────────────────────────────────

PROJECT_ID = os.environ.get("PIPELINE_PROJECT", "euro-football-analytics-20-25")
DATASET_ID = os.environ.get("PIPELINE_RAW_DS", "eu_football_raw")
TABLE_ID = "raw_matches"
BUCKET_NAME = os.environ.get("PIPELINE_BUCKET", "eu-football-raw-20-25")
GCS_URI = f"gs://{BUCKET_NAME}/raw/Matches.csv"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = [
    bigquery.SchemaField("Division",    "STRING"),
    bigquery.SchemaField("MatchDate",   "DATE"),
    bigquery.SchemaField("MatchTime",   "STRING"),
    bigquery.SchemaField("HomeTeam",    "STRING"),
    bigquery.SchemaField("AwayTeam",    "STRING"),
    bigquery.SchemaField("HomeElo",     "FLOAT64"),
    bigquery.SchemaField("AwayElo",     "FLOAT64"),
    bigquery.SchemaField("Form3Home",   "FLOAT64"),
    bigquery.SchemaField("Form5Home",   "FLOAT64"),
    bigquery.SchemaField("Form3Away",   "FLOAT64"),
    bigquery.SchemaField("Form5Away",   "FLOAT64"),
    bigquery.SchemaField("FTHome",      "FLOAT64"),
    bigquery.SchemaField("FTAway",      "FLOAT64"),
    bigquery.SchemaField("FTResult",    "STRING"),
    bigquery.SchemaField("HTHome",      "FLOAT64"),
    bigquery.SchemaField("HTAway",      "FLOAT64"),
    bigquery.SchemaField("HTResult",    "STRING"),
    bigquery.SchemaField("HomeShots",   "FLOAT64"),
    bigquery.SchemaField("AwayShots",   "FLOAT64"),
    bigquery.SchemaField("HomeTarget",  "FLOAT64"),
    bigquery.SchemaField("AwayTarget",  "FLOAT64"),
    bigquery.SchemaField("HomeFouls",   "FLOAT64"),
    bigquery.SchemaField("AwayFouls",   "FLOAT64"),
    bigquery.SchemaField("HomeCorners", "FLOAT64"),
    bigquery.SchemaField("AwayCorners", "FLOAT64"),
    bigquery.SchemaField("HomeYellow",  "FLOAT64"),
    bigquery.SchemaField("AwayYellow",  "FLOAT64"),
    bigquery.SchemaField("HomeRed",     "FLOAT64"),
    bigquery.SchemaField("AwayRed",     "FLOAT64"),
    bigquery.SchemaField("OddHome",     "FLOAT64"),
    bigquery.SchemaField("OddDraw",     "FLOAT64"),
    bigquery.SchemaField("OddAway",     "FLOAT64"),
    bigquery.SchemaField("MaxHome",     "FLOAT64"),
    bigquery.SchemaField("MaxDraw",     "FLOAT64"),
    bigquery.SchemaField("MaxAway",     "FLOAT64"),
    bigquery.SchemaField("Over25",      "FLOAT64"),
    bigquery.SchemaField("Under25",     "FLOAT64"),
    bigquery.SchemaField("MaxOver25",   "FLOAT64"),
    bigquery.SchemaField("MaxUnder25",  "FLOAT64"),
    bigquery.SchemaField("HandiSize",   "FLOAT64"),
    bigquery.SchemaField("HandiHome",   "FLOAT64"),
    bigquery.SchemaField("HandiAway",   "FLOAT64"),
    bigquery.SchemaField("C_LTH",       "FLOAT64"),
    bigquery.SchemaField("C_LTA",       "FLOAT64"),
    bigquery.SchemaField("C_VHD",       "FLOAT64"),
    bigquery.SchemaField("C_VAD",       "FLOAT64"),
    bigquery.SchemaField("C_HTB",       "FLOAT64"),
    bigquery.SchemaField("C_PHB",       "FLOAT64"),
]

# ── Main ──────────────────────────────────────────────────────────────────────

def create_external_table() -> None:
    """
    Create (or recreate) a BigQuery external table over the raw GCS CSV file.

    The table is always recreated (if_exists_action=REPLACE) to ensure the
    schema and GCS URI are always in sync with this script.
    """
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [GCS_URI]
    external_config.schema = SCHEMA
    external_config.options.skip_leading_rows = 1      # skip header row
    external_config.options.allow_quoted_newlines = True
    external_config.options.allow_jagged_rows = False

    table = bigquery.Table(table_ref, schema=SCHEMA)
    table.external_data_configuration = external_config

    logger.info("Creating external table: %s", table_ref)
    logger.info("Pointing to: %s", GCS_URI)

    # WRITE_TRUNCATE equivalent for external tables: delete and recreate
    client.delete_table(table_ref, not_found_ok=True)
    client.create_table(table)

    logger.info("External table created successfully: %s", table_ref)


if __name__ == "__main__":
    create_external_table()