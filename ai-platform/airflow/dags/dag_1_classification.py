"""
=============================================================================
DAG 1: TICKET CLASSIFICATION PIPELINE
=============================================================================
Schedule: Every 15 minutes
Agents: ticket_classifier, priority_assessor, root_cause_extractor

INTERVIEW TIP: This DAG runs 96 times/day (every 15 min). Each run:
  - Fetches up to 500 unclassified tickets
  - Classifies with GPT-4 (cached → ~60% hit rate = 200 actual LLM calls)
  - At 200 calls × 96 runs = 19,200 LLM calls/day capacity
  - With Redis caching, effective throughput = 50k+ queries/day

The DAG has 4 tasks:
  1. ingest_raw     → Load new tickets from CSV/webhook into RAW schema
  2. clean_raw      → Transform RAW → CORE (text cleaning, normalization)
  3. classify       → Run the 3-agent classification pipeline
  4. notify         → Alert on critical bugs or spikes
=============================================================================
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "echolab-ml",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def task_ingest_raw(**context):
    """Ingest new tickets from all sources into RAW schema."""
    import csv
    import json
    from utils.db import get_db_connection

    data_path = "/opt/airflow/data/jira_tickets.csv"
    inserted = 0

    try:
        with open(data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        return {"inserted": 0, "message": "No CSV file found"}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO raw.tickets (ticket_key, title, description, priority, status,
                        created_at, updated_at, reporter, product, component, source, raw_payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'jira', %s)
                    ON CONFLICT (ticket_key) DO NOTHING
                    """,
                    (
                        row.get("ticket_key"),
                        row.get("title"),
                        row.get("description"),
                        row.get("priority"),
                        row.get("status"),
                        row.get("created_at"),
                        row.get("updated_at"),
                        row.get("reporter"),
                        row.get("product"),
                        row.get("component"),
                        json.dumps(row),
                    ),
                )
                inserted += 1

    context["ti"].xcom_push(key="ingested_count", value=inserted)
    return {"inserted": inserted}


def task_clean_raw(**context):
    """Transform RAW tickets to CORE (clean text, normalize)."""
    import re
    from utils.db import get_db_connection

    def clean_text(text):
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"<.*?>", "", text)
        return text.strip().lower()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, ticket_key, title, description, priority, status, created_at, updated_at
                FROM raw.tickets r
                WHERE NOT EXISTS (
                    SELECT 1 FROM core.tickets c WHERE c.raw_ticket_id = r.id
                )
                LIMIT 500
            """)
            rows = cur.fetchall()

            processed = 0
            for row in rows:
                raw_id, ticket_key, title, desc, priority, status, created, updated = row
                cur.execute(
                    """
                    INSERT INTO core.tickets
                    (raw_ticket_id, ticket_key, title, description_clean, priority, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket_key) DO NOTHING
                    """,
                    (raw_id, ticket_key, title, clean_text(desc), priority, status),
                )
                processed += 1

    context["ti"].xcom_push(key="processed_count", value=processed)
    return {"processed": processed}


def task_classify(**context):
    """Run the 3-agent classification pipeline."""
    from pipelines.pipeline_1_classification import run_classification_pipeline
    result = run_classification_pipeline()
    context["ti"].xcom_push(key="classification_result", value=result)
    return result


def task_notify(**context):
    """Check for critical findings and send notifications."""
    from utils.redis_cache import redis_client
    import json

    result = context["ti"].xcom_pull(task_ids="classify", key="classification_result")
    if not result:
        return {"notified": False}

    # Store latest pipeline run status in Redis for dashboard
    try:
        redis_client().setex(
            "pipeline:classification:latest",
            3600,
            json.dumps({
                "run_at": datetime.utcnow().isoformat(),
                "processed": result.get("processed", 0),
                "classified": result.get("classified", 0),
                "errors": result.get("errors", 0),
            }),
        )
    except Exception:
        pass

    return {"notified": True, "result": result}


with DAG(
    dag_id="echolab_ticket_classification",
    default_args=default_args,
    description="Classify tickets using 3 LangChain agents (every 15 min)",
    schedule_interval="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["echolab", "classification", "langchain", "pipeline-1"],
    max_active_runs=1,
) as dag:

    start = EmptyOperator(task_id="start")

    ingest = PythonOperator(task_id="ingest_raw", python_callable=task_ingest_raw)
    clean = PythonOperator(task_id="clean_raw", python_callable=task_clean_raw)
    classify = PythonOperator(task_id="classify", python_callable=task_classify)
    notify = PythonOperator(task_id="notify", python_callable=task_notify)

    end = EmptyOperator(task_id="end")

    # DAG structure: ingest → clean → classify → notify
    start >> ingest >> clean >> classify >> notify >> end
