#!/bin/bash
# =============================================================================
# ECHOLAB AI PLATFORM - STARTUP SCRIPT
# =============================================================================
# Usage: ./start.sh
#
# This script starts the entire Echolab AI platform:
# 1. PostgreSQL + pgvector
# 2. Redis
# 3. Qdrant
# 4. Airflow (webserver + scheduler + worker + flower)
# 5. FastAPI backend
# =============================================================================

set -e

echo "============================================"
echo "  ECHOLAB AI PLATFORM - Starting Services"
echo "============================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Create required directories
mkdir -p airflow/logs airflow/plugins airflow/config models

# Set Airflow UID
echo "AIRFLOW_UID=$(id -u)" >> .env 2>/dev/null || echo "AIRFLOW_UID=50000" >> .env

# Initialize Airflow database
echo "Initializing Airflow..."
docker compose up airflow-init --build

# Start all services
echo "Starting all services..."
docker compose up -d --build

echo ""
echo "============================================"
echo "  ECHOLAB AI PLATFORM - Services Running"
echo "============================================"
echo ""
echo "  Airflow UI:     http://localhost:8080  (admin/admin)"
echo "  FastAPI:         http://localhost:8000/docs"
echo "  Flower:          http://localhost:5555"
echo "  Qdrant:          http://localhost:6333/dashboard"
echo "  PostgreSQL:      localhost:5432"
echo "  Redis:           localhost:6379"
echo ""
echo "  To stop: docker compose down"
echo "  To view logs: docker compose logs -f"
echo "============================================"
