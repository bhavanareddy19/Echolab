"""
=============================================================================
DAG 3: RAG-POWERED HYPOTHESIS GENERATION (LangGraph)
=============================================================================
Schedule: Every 6 hours
Agents: context_retriever, hypothesis_generator, experiment_designer
=============================================================================
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "echolab-ml",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}


def task_run_hypothesis_pipeline(**context):
    """Run the LangGraph hypothesis generation workflow."""
    from pipelines.pipeline_3_rag_hypothesis import run_hypothesis_pipeline
    result = run_hypothesis_pipeline()
    context["ti"].xcom_push(key="hypothesis_result", value=result)
    return result


def task_sync_to_growthbook(**context):
    """Sync approved hypotheses to GrowthBook for A/B testing."""
    from utils.db import fetch_all, execute_query
    import json
    import logging
    import os
    import httpx

    logger = logging.getLogger(__name__)

    hypotheses = fetch_all("""
        SELECT h.id, h.hypothesis_text, h.experiment_config, h.confidence_score,
               c.cluster_label
        FROM analytics.hypotheses h
        JOIN analytics.clusters c ON h.cluster_id = c.id
        WHERE h.status = 'draft' AND h.confidence_score > 0.7
        ORDER BY h.confidence_score DESC
        LIMIT 5
    """)

    if not hypotheses:
        return {"synced": 0}

    growthbook_url = os.getenv("GROWTHBOOK_API_URL", "https://api.growthbook.io")
    growthbook_pat = os.getenv("GROWTHBOOK_PAT", "")

    synced_ids = []
    for h in hypotheses:
        config = h.get("experiment_config") or {}
        if isinstance(config, str):
            config = json.loads(config)

        tracking_key = f"echolab-{h['cluster_label'].lower().replace(' ', '-')}-{h['id']}"

        payload = {
            "name": f"[Echolab] {h['cluster_label']}: {h['hypothesis_text'][:80]}",
            "trackingKey": tracking_key,
            "hypothesis": h["hypothesis_text"],
            "description": f"Auto-generated from pain point cluster: {h['cluster_label']}",
            "variations": [
                {"name": "Control", "description": config.get("variant_a", "Current implementation"), "key": "0"},
                {"name": "Variant", "description": config.get("variant_b", "Proposed change"), "key": "1"},
            ],
            "metrics": [config.get("primary_metric", "conversion_rate")],
        }

        if not growthbook_pat:
            logger.warning("GROWTHBOOK_PAT not set - skipping GrowthBook sync, marking as synced locally")
            synced_ids.append(h["id"])
            continue

        try:
            resp = httpx.post(
                f"{growthbook_url}/api/v1/experiments",
                headers={"Authorization": f"Bearer {growthbook_pat}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Synced hypothesis {h['id']} to GrowthBook: {tracking_key}")
                synced_ids.append(h["id"])
            else:
                logger.warning(f"GrowthBook sync failed for {h['id']}: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            logger.error(f"GrowthBook API error for hypothesis {h['id']}: {e}")

    # Mark synced hypotheses as 'experiment' status
    for hid in synced_ids:
        execute_query(
            "UPDATE analytics.hypotheses SET status = 'experiment' WHERE id = %s",
            (hid,),
        )

    return {"synced": len(synced_ids), "hypotheses": synced_ids}


with DAG(
    dag_id="echolab_hypothesis_generation",
    default_args=default_args,
    description="Generate hypotheses using LangGraph RAG workflow (every 6h)",
    schedule_interval="0 */6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["echolab", "rag", "langgraph", "hypothesis", "pipeline-3"],
    max_active_runs=1,
) as dag:

    start = EmptyOperator(task_id="start")
    generate = PythonOperator(task_id="generate_hypotheses", python_callable=task_run_hypothesis_pipeline)
    sync = PythonOperator(task_id="sync_to_growthbook", python_callable=task_sync_to_growthbook)
    end = EmptyOperator(task_id="end")

    start >> generate >> sync >> end
