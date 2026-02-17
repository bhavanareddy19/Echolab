"""
=============================================================================
DAG 2: SEMANTIC CLUSTERING & PAIN POINT DISCOVERY
=============================================================================
Schedule: Every 2 hours
Agents: embedding_generator, cluster_analyzer, pain_point_synthesizer
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
    "retry_delay": timedelta(minutes=10),
}


def task_generate_embeddings(**context):
    """Generate embeddings for all tickets without them."""
    from pipelines.pipeline_2_clustering import generate_embeddings
    from utils.db import fetch_all, get_db_connection

    tickets = fetch_all("""
        SELECT id, title, description_clean
        FROM core.tickets
        WHERE embedding IS NULL AND feature_type IS NOT NULL
        LIMIT 2000
    """)

    if not tickets:
        return {"embedded": 0}

    texts = [f"{t['title']} {t['description_clean'] or ''}" for t in tickets]
    embeddings = generate_embeddings(texts)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for i, ticket in enumerate(tickets):
                cur.execute(
                    "UPDATE core.tickets SET embedding = %s WHERE id = %s",
                    (str(embeddings[i].tolist()), ticket["id"]),
                )

    context["ti"].xcom_push(key="embedded_count", value=len(tickets))
    return {"embedded": len(tickets)}


def task_cluster(**context):
    """Run clustering pipeline."""
    from pipelines.pipeline_2_clustering import run_clustering_pipeline
    result = run_clustering_pipeline()
    context["ti"].xcom_push(key="cluster_result", value=result)
    return result


def task_update_faiss_index(**context):
    """Rebuild FAISS index with latest embeddings."""
    import numpy as np
    from pipelines.pipeline_2_clustering import build_faiss_index
    from utils.db import fetch_all
    import faiss
    import os

    tickets = fetch_all("""
        SELECT id, embedding FROM core.tickets
        WHERE embedding IS NOT NULL
        ORDER BY id
    """)

    if not tickets:
        return {"indexed": 0}

    # Convert string embeddings to numpy array
    embeddings = []
    for t in tickets:
        emb = t["embedding"]
        if isinstance(emb, str):
            emb = eval(emb)  # Parse string representation
        embeddings.append(emb)

    embeddings_np = np.array(embeddings, dtype=np.float32)
    index = build_faiss_index(embeddings_np)

    # Save index to disk for other services
    index_path = "/opt/airflow/models/tickets.faiss"
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    faiss.write_index(index, index_path)

    return {"indexed": len(tickets), "path": index_path}


with DAG(
    dag_id="echolab_semantic_clustering",
    default_args=default_args,
    description="Cluster tickets using embeddings + FAISS (every 2 hours)",
    schedule_interval="0 */2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["echolab", "clustering", "faiss", "embeddings", "pipeline-2"],
    max_active_runs=1,
) as dag:

    start = EmptyOperator(task_id="start")
    embed = PythonOperator(task_id="generate_embeddings", python_callable=task_generate_embeddings)
    cluster = PythonOperator(task_id="cluster_tickets", python_callable=task_cluster)
    index = PythonOperator(task_id="update_faiss_index", python_callable=task_update_faiss_index)
    end = EmptyOperator(task_id="end")

    start >> embed >> cluster >> index >> end
