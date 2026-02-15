# Running Echolab - Quick Start Guide

## Prerequisites
- Docker Desktop installed and running
- Python 3.10+ with venv
- Node.js 20+ with npm

## Method 1: Local Development (Recommended)

### 1. Start Database Services (Docker)
```bash
cd ai-platform
docker compose up -d postgres redis qdrant
```

### 2. Start Backend (Local Python)
```bash
cd ai-platform/backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the backend
uvicorn main:app --reload --host 0.0.0.0
```

Backend will be available at: http://localhost:8000

### 3. Start Frontend (Local Node.js)
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run the frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Method 2: Full Docker (All Services)

```bash
cd ai-platform
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Qdrant on port 6333
- Backend API on port 8000
- Airflow Webserver on port 8080
- Flower on port 5555

**Note**: Frontend is not in Docker yet. Run it separately with Method 1, step 3.

## Verify Everything is Working

1. **Check Database**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok","postgres":"ok","redis":"ok"}`

2. **Check API**:
   ```bash
   curl http://localhost:8000/api/dashboard/stats
   ```
   Should return JSON with ticket counts, clusters, hypotheses

3. **Open Frontend**:
   Navigate to http://localhost:3000
   - You should see the dashboard with real data
   - Click "Tickets" to see the ticket list
   - Click "Pain Points" to see clusters

## Troubleshooting

### Backend can't connect to database
- Error: `could not translate host name "postgres" to address`
- Solution: Make sure `backend/.env.local` exists with `POSTGRES_HOST=localhost`

### Database not initialized
- Run: `docker compose down -v` then `docker compose up -d postgres redis qdrant`
- This recreates the database with seed data

### Frontend shows "Failed to load"
- Check backend is running on http://localhost:8000
- Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Port already in use
- PostgreSQL (5432): Stop any local PostgreSQL service
- Backend (8000): Kill any other process using port 8000
- Frontend (3000): Kill any other Next.js dev server

## Environment Files

### Backend: `ai-platform/backend/.env.local`
```
POSTGRES_HOST=localhost
POSTGRES_USER=echolab
POSTGRES_PASSWORD=echolab_secret_2024
POSTGRES_DB=echolab
REDIS_HOST=localhost
```

### Frontend: `frontend/.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Stop Services

```bash
# Stop Docker services
cd ai-platform
docker compose down

# Stop backend: Press Ctrl+C in backend terminal
# Stop frontend: Press Ctrl+C in frontend terminal
```

## Database Access

Connect to PostgreSQL directly:
```bash
docker exec -it echolab-postgres psql -U echolab -d echolab

# View tables
\dt raw.*
\dt core.*
\dt analytics.*

# View seed data
SELECT * FROM raw.tickets LIMIT 5;
SELECT * FROM analytics.clusters;
SELECT * FROM analytics.hypotheses;
```

## Demo Data

The database is seeded with:
- 20 sample tickets in `raw.tickets`
- 20 classified tickets in `core.tickets`
- 5 pain point clusters in `analytics.clusters`
- 6 hypotheses in `analytics.hypotheses`
- 15 AI agents in `agents.registry`

## Features Available

✅ Dashboard with real-time stats
✅ Ticket management (create, view, edit, delete)
✅ CSV bulk upload
✅ Ticket classification (rule-based, no API keys needed)
✅ Pain point clusters view
✅ Hypothesis generation and editing
✅ Experiments tracking
✅ Agent registry

## Next Steps

1. Customize the classification rules in `classify_ticket()` function
2. Add your own tickets via CSV upload or manual entry
3. Run analysis to classify new tickets
4. Explore pain points and generate hypotheses
