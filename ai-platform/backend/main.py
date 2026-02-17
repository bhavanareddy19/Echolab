import os
import csv
import io
import json
import re
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import redis
from dotenv import load_dotenv

# Load .env.local if it exists (for local development), otherwise load .env
env_local = Path(__file__).parent / '.env.local'
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

app = FastAPI(title="Ticket AI Platform")

# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Environment Variables
# -----------------------------
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ticket_ai")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# -----------------------------
# Database Connection
# -----------------------------
def pg_conn():
    return psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# -----------------------------
# Pydantic Models
# -----------------------------
class TicketCreate(BaseModel):
    ticket_key: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "Open"
    reporter: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    reporter: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None

class HypothesisCreate(BaseModel):
    cluster_id: Optional[int] = None
    hypothesis_text: str
    confidence_score: Optional[float] = None
    expected_impact: Optional[str] = "medium"
    experiment_config: Optional[dict] = None
    status: Optional[str] = "draft"

class HypothesisUpdate(BaseModel):
    hypothesis_text: Optional[str] = None
    confidence_score: Optional[float] = None
    expected_impact: Optional[str] = None
    experiment_config: Optional[dict] = None
    status: Optional[str] = None

# -----------------------------
# Helpers
# -----------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def classify_ticket(title: str, description: str) -> dict:
    """Rule-based classification for tickets (no LLM needed)."""
    text = f"{title} {description}".lower()

    # Feature type classification
    feature_type = "improvement"
    bug_keywords = ["bug", "error", "crash", "broken", "fail", "not working", "issue", "exception", "fix"]
    feature_keywords = ["feature", "request", "add", "new", "want", "need", "enhance", "wish"]
    if any(kw in text for kw in bug_keywords):
        feature_type = "bug"
    elif any(kw in text for kw in feature_keywords):
        feature_type = "feature"

    # Sentiment
    sentiment = "neutral"
    negative_words = ["frustrated", "angry", "terrible", "awful", "worst", "hate", "unacceptable", "annoyed", "disappointed", "useless"]
    positive_words = ["great", "love", "amazing", "excellent", "good", "helpful", "thanks", "appreciate"]
    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"

    # Urgency score (0-1)
    urgency = 0.5
    high_urgency = ["critical", "urgent", "asap", "immediately", "blocker", "production", "down", "outage"]
    low_urgency = ["minor", "cosmetic", "nice to have", "when possible", "low priority"]
    if any(kw in text for kw in high_urgency):
        urgency = 0.9
    elif any(kw in text for kw in low_urgency):
        urgency = 0.2

    # Customer problem extraction (first sentence or first 200 chars)
    customer_problem = description[:200] if description else title

    # Root cause guess
    root_cause = None
    if "timeout" in text or "slow" in text:
        root_cause = "Performance degradation - possible backend latency or resource exhaustion"
    elif "crash" in text or "exception" in text:
        root_cause = "Unhandled exception in application logic"
    elif "login" in text or "auth" in text or "password" in text:
        root_cause = "Authentication/authorization flow issue"
    elif "ui" in text or "display" in text or "layout" in text:
        root_cause = "Frontend rendering issue"

    # Cluster assignment based on keywords
    cluster_id = None
    if "checkout" in text or "payment" in text or "cart" in text:
        cluster_id = 1
    elif "slow" in text or "performance" in text or "timeout" in text or "loading" in text:
        cluster_id = 2
    elif "export" in text or "download" in text or "csv" in text or "report" in text:
        cluster_id = 3
    elif "login" in text or "auth" in text or "password" in text or "sso" in text:
        cluster_id = 4
    elif "ui" in text or "display" in text or "layout" in text or "button" in text:
        cluster_id = 5

    return {
        "feature_type": feature_type,
        "sentiment": sentiment,
        "urgency_score": urgency,
        "customer_problem": customer_problem,
        "root_cause": root_cause,
        "cluster_id": cluster_id,
    }

# -----------------------------
# Health Check
# -----------------------------
@app.get("/health")
def health():
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            _ = cur.fetchone()

    r.ping()

    return {"status": "ok", "postgres": "ok", "redis": "ok"}

# =============================================
# TICKETS ENDPOINTS
# =============================================

@app.post("/api/tickets")
def create_ticket(ticket: TicketCreate):
    """Create a single ticket in raw.tickets."""
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO raw.tickets (ticket_key, title, description, priority, status, reporter, product, component, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (ticket.ticket_key, ticket.title, ticket.description, ticket.priority,
                  ticket.status, ticket.reporter, ticket.product, ticket.component))
            new_id = cur.fetchone()[0]
        conn.commit()
    return {"id": new_id, "ticket_key": ticket.ticket_key, "message": "Ticket created"}

@app.post("/api/tickets/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file to bulk-insert tickets into raw.tickets."""
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    inserted = 0
    with pg_conn() as conn:
        with conn.cursor() as cur:
            for row in reader:
                ticket_key = row.get("ticket_key", row.get("key", f"UPLOAD-{inserted+1}"))
                title = row.get("title", row.get("summary", ""))
                description = row.get("description", "")
                priority = row.get("priority", "Medium")
                status = row.get("status", "Open")
                reporter = row.get("reporter", None)
                product = row.get("product", None)
                component = row.get("component", None)

                cur.execute("""
                    INSERT INTO raw.tickets (ticket_key, title, description, priority, status, reporter, product, component, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (ticket_key) DO NOTHING
                """, (ticket_key, title, description, priority, status, reporter, product, component))
                inserted += 1
        conn.commit()
    return {"inserted": inserted, "filename": file.filename}

@app.get("/api/tickets")
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    priority: Optional[str] = None,
    status: Optional[str] = None,
    feature_type: Optional[str] = None,
    search: Optional[str] = None,
):
    """List tickets with pagination and filtering. Joins raw + core for classification data."""
    offset = (page - 1) * page_size

    where_clauses = []
    params = []

    if priority:
        where_clauses.append("r.priority = %s")
        params.append(priority)
    if status:
        where_clauses.append("r.status = %s")
        params.append(status)
    if feature_type:
        where_clauses.append("c.feature_type = %s")
        params.append(feature_type)
    if search:
        where_clauses.append("(r.title ILIKE %s OR r.description ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get total count
            cur.execute(f"""
                SELECT COUNT(*) as total
                FROM raw.tickets r
                LEFT JOIN core.tickets c ON r.ticket_key = c.ticket_key
                {where_sql}
            """, params)
            total = cur.fetchone()["total"]

            # Get page
            cur.execute(f"""
                SELECT r.id, r.ticket_key, r.title, r.description, r.priority, r.status,
                       r.reporter, r.product, r.component, r.created_at, r.updated_at,
                       c.feature_type, c.sentiment, c.urgency_score, c.customer_problem,
                       c.root_cause, c.cluster_id
                FROM raw.tickets r
                LEFT JOIN core.tickets c ON r.ticket_key = c.ticket_key
                {where_sql}
                ORDER BY r.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            tickets = cur.fetchall()

    return {
        "tickets": [dict(t) for t in tickets],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
    }

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    """Get a single ticket with classification results."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT r.id, r.ticket_key, r.title, r.description, r.priority, r.status,
                       r.reporter, r.product, r.component, r.created_at, r.updated_at,
                       c.feature_type, c.sentiment, c.urgency_score, c.customer_problem,
                       c.root_cause, c.cluster_id, c.cluster_confidence
                FROM raw.tickets r
                LEFT JOIN core.tickets c ON r.ticket_key = c.ticket_key
                WHERE r.id = %s
            """, (ticket_id,))
            ticket = cur.fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return dict(ticket)

@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: int, update: TicketUpdate):
    """Update a ticket in raw.tickets."""
    fields = []
    values = []
    for field_name, value in update.model_dump(exclude_none=True).items():
        fields.append(f"{field_name} = %s")
        values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(ticket_id)
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE raw.tickets SET {', '.join(fields)}, updated_at = NOW()
                WHERE id = %s
            """, values)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Ticket not found")
        conn.commit()
    return {"message": "Ticket updated", "id": ticket_id}

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    """Delete a ticket from raw.tickets (and cascade to core)."""
    with pg_conn() as conn:
        with conn.cursor() as cur:
            # Delete from core first (FK reference)
            cur.execute("DELETE FROM core.tickets WHERE raw_ticket_id = %s", (ticket_id,))
            cur.execute("DELETE FROM raw.tickets WHERE id = %s", (ticket_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Ticket not found")
        conn.commit()
    return {"message": "Ticket deleted", "id": ticket_id}

# =============================================
# DASHBOARD ENDPOINTS
# =============================================

@app.get("/api/dashboard/stats")
def dashboard_stats():
    """Aggregated stats for the dashboard overview."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Total tickets
            cur.execute("SELECT COUNT(*) as count FROM raw.tickets")
            ticket_count = cur.fetchone()["count"]

            # Classified tickets
            cur.execute("SELECT COUNT(*) as count FROM core.tickets")
            classified_count = cur.fetchone()["count"]

            # Pain points (clusters)
            cur.execute("SELECT COUNT(*) as count FROM analytics.clusters WHERE status = 'active'")
            cluster_count = cur.fetchone()["count"]

            # Hypotheses
            cur.execute("SELECT COUNT(*) as count FROM analytics.hypotheses")
            hypothesis_count = cur.fetchone()["count"]

            # Experiments (hypotheses with status 'experiment' or 'testing')
            cur.execute("SELECT COUNT(*) as count FROM analytics.hypotheses WHERE status IN ('experiment', 'testing')")
            experiment_count = cur.fetchone()["count"]

            # Feature vs Bug counts from core.tickets
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN feature_type = 'feature' THEN 1 ELSE 0 END), 0) as features,
                    COALESCE(SUM(CASE WHEN feature_type = 'bug' THEN 1 ELSE 0 END), 0) as bugs,
                    COALESCE(SUM(CASE WHEN feature_type = 'improvement' THEN 1 ELSE 0 END), 0) as improvements
                FROM core.tickets
            """)
            type_counts = cur.fetchone()

            # Status breakdown
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM raw.tickets
                GROUP BY status
            """)
            status_rows = cur.fetchall()
            status_breakdown = {row["status"]: row["count"] for row in status_rows}

    result = {
        "ticket_count": ticket_count,
        "classified_count": classified_count,
        "cluster_count": cluster_count,
        "hypothesis_count": hypothesis_count,
        "experiment_count": experiment_count,
        "features": type_counts["features"],
        "bugs": type_counts["bugs"],
        "improvements": type_counts["improvements"],
        "status_breakdown": status_breakdown,
    }

    # Calculate month-over-month change dynamically
    with pg_conn() as conn2:
        with conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur2:
            cur2.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as this_month,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '60 days'
                                     AND created_at < NOW() - INTERVAL '30 days') as last_month
                FROM raw.tickets
            """)
            mom = cur2.fetchone()
            this_m = mom["this_month"] or 0
            last_m = mom["last_month"] or 0
            if last_m > 0:
                pct = round(((this_m - last_m) / last_m) * 100)
                result["change_vs_last_month"] = f"{'+' if pct >= 0 else ''}{pct}%"
            else:
                result["change_vs_last_month"] = "N/A"

    return result

# =============================================
# CLUSTERS (PAIN POINTS) ENDPOINTS
# =============================================

@app.get("/api/clusters")
def list_clusters():
    """List all clusters with ticket counts."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT cl.id, cl.cluster_label, cl.description, cl.num_tickets,
                       cl.avg_urgency, cl.top_keywords, cl.status, cl.created_at,
                       COUNT(ct.id) as actual_ticket_count
                FROM analytics.clusters cl
                LEFT JOIN core.tickets ct ON ct.cluster_id = cl.id
                GROUP BY cl.id
                ORDER BY cl.num_tickets DESC
            """)
            clusters = cur.fetchall()
    return {"clusters": [dict(c) for c in clusters]}

@app.get("/api/clusters/{cluster_id}")
def get_cluster(cluster_id: int):
    """Get cluster detail with associated tickets."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, cluster_label, description, num_tickets, avg_urgency,
                       top_keywords, status, created_at
                FROM analytics.clusters
                WHERE id = %s
            """, (cluster_id,))
            cluster = cur.fetchone()
            if not cluster:
                raise HTTPException(status_code=404, detail="Cluster not found")

            cur.execute("""
                SELECT c.id, c.ticket_key, c.title, c.feature_type, c.sentiment,
                       c.urgency_score, c.customer_problem
                FROM core.tickets c
                WHERE c.cluster_id = %s
                ORDER BY c.urgency_score DESC NULLS LAST
            """, (cluster_id,))
            tickets = cur.fetchall()

    result = dict(cluster)
    result["tickets"] = [dict(t) for t in tickets]
    return result

# =============================================
# HYPOTHESES ENDPOINTS
# =============================================

@app.get("/api/hypotheses")
def list_hypotheses():
    """List all hypotheses with cluster info."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT h.id, h.cluster_id, h.hypothesis_text, h.confidence_score,
                       h.expected_impact, h.experiment_config, h.status, h.created_at,
                       cl.cluster_label
                FROM analytics.hypotheses h
                LEFT JOIN analytics.clusters cl ON h.cluster_id = cl.id
                ORDER BY h.confidence_score DESC NULLS LAST
            """)
            hypotheses = cur.fetchall()
    return {"hypotheses": [dict(h) for h in hypotheses]}

@app.get("/api/hypotheses/{hypothesis_id}")
def get_hypothesis(hypothesis_id: int):
    """Get a single hypothesis with detail."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT h.id, h.cluster_id, h.hypothesis_text, h.confidence_score,
                       h.expected_impact, h.experiment_config, h.status, h.created_at,
                       cl.cluster_label
                FROM analytics.hypotheses h
                LEFT JOIN analytics.clusters cl ON h.cluster_id = cl.id
                WHERE h.id = %s
            """, (hypothesis_id,))
            hypothesis = cur.fetchone()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return dict(hypothesis)

@app.post("/api/hypotheses")
def create_hypothesis(hyp: HypothesisCreate):
    """Create a new hypothesis."""
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO analytics.hypotheses (cluster_id, hypothesis_text, confidence_score,
                    expected_impact, experiment_config, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (hyp.cluster_id, hyp.hypothesis_text, hyp.confidence_score,
                  hyp.expected_impact, json.dumps(hyp.experiment_config) if hyp.experiment_config else None,
                  hyp.status))
            new_id = cur.fetchone()[0]
        conn.commit()
    return {"id": new_id, "message": "Hypothesis created"}

@app.put("/api/hypotheses/{hypothesis_id}")
def update_hypothesis(hypothesis_id: int, update: HypothesisUpdate):
    """Update a hypothesis."""
    fields = []
    values = []
    for field_name, value in update.model_dump(exclude_none=True).items():
        if field_name == "experiment_config" and value is not None:
            fields.append(f"{field_name} = %s")
            values.append(json.dumps(value))
        else:
            fields.append(f"{field_name} = %s")
            values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(hypothesis_id)
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE analytics.hypotheses SET {', '.join(fields)}
                WHERE id = %s
            """, values)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Hypothesis not found")
        conn.commit()
    return {"message": "Hypothesis updated", "id": hypothesis_id}

# =============================================
# ANALYSIS TRIGGER
# =============================================

@app.post("/api/analyze")
def analyze_tickets():
    """Classify and process unprocessed tickets from raw -> core.
    Uses rule-based classification (no LLM/API keys needed)."""
    processed = 0
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Find raw tickets not yet in core
            cur.execute("""
                SELECT r.id, r.ticket_key, r.title, r.description, r.priority,
                       r.status, r.product, r.component
                FROM raw.tickets r
                LEFT JOIN core.tickets c ON r.ticket_key = c.ticket_key
                WHERE c.id IS NULL
            """)
            unprocessed = cur.fetchall()

            for row in unprocessed:
                classification = classify_ticket(row["title"], row["description"] or "")

                cur.execute("""
                    INSERT INTO core.tickets (
                        raw_ticket_id, ticket_key, title, description_clean, priority, status,
                        product, component, feature_type, sentiment, urgency_score,
                        customer_problem, root_cause, cluster_id, classified_at, classified_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'rule_engine')
                    ON CONFLICT (ticket_key) DO NOTHING
                """, (
                    row["id"], row["ticket_key"], row["title"],
                    clean_text(row["description"] or ""),
                    row["priority"], row["status"], row["product"], row["component"],
                    classification["feature_type"], classification["sentiment"],
                    classification["urgency_score"], classification["customer_problem"],
                    classification["root_cause"], classification["cluster_id"],
                ))
                processed += 1

            # Update cluster ticket counts
            cur.execute("""
                UPDATE analytics.clusters cl
                SET num_tickets = sub.cnt
                FROM (
                    SELECT cluster_id, COUNT(*) as cnt
                    FROM core.tickets
                    WHERE cluster_id IS NOT NULL
                    GROUP BY cluster_id
                ) sub
                WHERE cl.id = sub.cluster_id
            """)

        conn.commit()
    return {"processed": processed, "message": f"Classified {processed} tickets"}

# =============================================
# AGENTS ENDPOINTS
# =============================================

@app.get("/api/agents")
def list_agents():
    """List all registered agents with stats."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, agent_name, agent_type, description, model_backend,
                       is_active, avg_latency_ms, success_rate, created_at
                FROM agents.registry
                ORDER BY id
            """)
            agents = cur.fetchall()
    return {"agents": [dict(a) for a in agents]}

# =============================================
# LEGACY ENDPOINTS (kept for compatibility)
# =============================================

@app.post("/ingest/csv")
def ingest_csv(path: str = "/app/data/jira_tickets.csv"):
    """Ingest tickets from a CSV file into raw.tickets."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found at {path}")

    if not rows:
        return {"inserted": 0}

    inserted = 0
    with pg_conn() as conn:
        with conn.cursor() as cur:
            for row in rows:
                ticket_key = row.get("ticket_key", f"CSV-{inserted+1}")
                cur.execute(
                    """
                    INSERT INTO raw.tickets (ticket_key, title, description, priority, status,
                        reporter, product, component, source, raw_payload, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'jira_csv', %s, NOW(), NOW())
                    ON CONFLICT (ticket_key) DO NOTHING
                    """,
                    (ticket_key, row.get("title", ""), row.get("description", ""),
                     row.get("priority", "Medium"), row.get("status", "Open"),
                     row.get("reporter"), row.get("product"), row.get("component"),
                     json.dumps(row)),
                )
                inserted += 1
        conn.commit()

    return {"inserted": inserted}

@app.get("/raw/count")
def raw_count():
    """Count raw tickets."""
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw.tickets;")
            (count,) = cur.fetchone()
    return {"raw_ticket_count": count}

@app.post("/process/raw-to-core")
def process_raw_to_core():
    """Process raw tickets into core (same as /api/analyze)."""
    return analyze_tickets()
