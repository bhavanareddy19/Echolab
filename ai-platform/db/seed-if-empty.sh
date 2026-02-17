#!/bin/bash
# Auto-seed database if it's empty
# This can be added to docker-compose.yml as a command

COUNT=$(psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT COUNT(*) FROM raw.tickets WHERE ticket_key LIKE 'ECHO-%'")

if [ "$COUNT" -eq "0" ]; then
    echo "Database is empty, seeding data..."
    psql -U $POSTGRES_USER -d $POSTGRES_DB -f /docker-entrypoint-initdb.d/02-airflow-init.sql
    echo "Seeding complete!"
else
    echo "Database already has $COUNT tickets, skipping seed"
fi
