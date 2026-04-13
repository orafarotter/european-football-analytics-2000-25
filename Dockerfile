# ---------------------------------------------------------------------------
# Base image: official Airflow 2.7.2 
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

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
