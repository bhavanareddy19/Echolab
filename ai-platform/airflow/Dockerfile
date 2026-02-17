# =============================================================================
# ECHOLAB AIRFLOW DOCKERFILE
# =============================================================================
# This Dockerfile builds a custom Airflow image with all ML/AI dependencies
# for running LLM pipelines, RAG systems, and multi-agent workflows.
#
# INTERVIEW TIP: We use apache/airflow as base and add ML libraries.
# The image is optimized for production with multi-stage builds.
# =============================================================================

FROM apache/airflow:2.8.1-python3.11

# Switch to root for system dependencies
USER root

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /opt/airflow
