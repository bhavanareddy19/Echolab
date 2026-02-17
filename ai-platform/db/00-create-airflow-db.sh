#!/bin/bash
set -e

# Create the airflow database for Airflow metadata
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE airflow;
EOSQL
