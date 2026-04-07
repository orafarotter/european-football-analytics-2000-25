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

COPY requirements.txt /requirements.txt

RUN curl -L "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt" \
    | grep -v "protobuf==" > /tmp/constraints.txt && \
    pip install --no-cache-dir "protobuf>=5.0.0,<6.0.0" "dbt-core==1.8.9" "dbt-bigquery==1.8.2" && \
    pip install --no-cache-dir --constraint /tmp/constraints.txt -r /requirements.txt