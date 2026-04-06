# Dockerfile — Custom Airflow image for the EU Football Analytics pipeline.
#
# Base: official Apache Airflow 2.10.5 image (matches the version used in the project).
# Adds: dbt-core, dbt-bigquery, kaggle, and the Google provider for Airflow.
#
# Build: docker compose build
# The image is built automatically by docker compose up --build.

FROM apache/airflow:2.10.5-python3.11

# Switch to root to install system dependencies (if any are needed in the future)
USER root

# Install any OS-level dependencies here if needed
# (none required for this project at this time)

# Switch back to the airflow user for pip installs (security best practice)
USER airflow

# Copy the requirements file and install Python dependencies
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt