#!/bin/bash
# System Verification Script for Echolab

echo "========================================="
echo "Echolab System Verification"
echo "========================================="
echo ""

# Check Docker containers
echo "1. Docker Containers Status:"
docker ps --filter "name=echolab" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
echo ""

# Check database
echo "2. Database Data:"
docker exec echolab-postgres psql -U echolab -d echolab -c "
SELECT
    (SELECT COUNT(*) FROM raw.tickets WHERE ticket_key LIKE 'ECHO-%') as raw_tickets,
    (SELECT COUNT(*) FROM core.tickets) as core_tickets,
    (SELECT COUNT(*) FROM analytics.clusters) as clusters,
    (SELECT COUNT(*) FROM analytics.hypotheses) as hypotheses;
" | head -5
echo ""

# Check backend API
echo "3. Backend API Health:"
curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "API not responding"
echo ""

# Check frontend
echo "4. Frontend:"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend is running on http://localhost:3000"
else
    echo "✗ Frontend is not running"
fi
echo ""

echo "========================================="
echo "Summary:"
echo "========================================="
echo "Database: http://localhost:5432"
echo "Backend API: http://localhost:8000"
echo "Backend API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo "Airflow: http://localhost:8080"
echo "========================================="
