# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Base image: official Airflow 2.10.5 on Python 3.11
# We install project dependencies here so the pip layer is cached by Docker
# and does NOT re-run on every `docker compose up`.
# ---------------------------------------------------------------------------
FROM apache/airflow:2.7.2


# Switch to root only to install OS-level deps (none needed here, but kept
# as a placeholder so future additions don't break the USER directive order)
USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the airflow user before any pip operations
USER airflow

# Copy requirements first — Docker caches this layer until the file changes,
# so rebuilds caused only by DAG edits won't re-run pip install.
COPY requirements.txt /requirements.txt

# Install project dependencies.
# No constraint file needed — the base image already ships Airflow
# with its dependencies locked; pip resolves the remaining packages freely.
RUN pip install --no-cache-dir -r /requirements.txt
