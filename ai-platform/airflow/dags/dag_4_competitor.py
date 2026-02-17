"""
=============================================================================
DAG 4: MULTI-AGENT COMPETITOR ANALYSIS (CrewAI)
=============================================================================
Schedule: Weekly (Mondays at 6 AM)
Agents: market_researcher, feature_gap_analyst, strategy_advisor
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
    "retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(hours=2),
}


def task_competitor_analysis(**context):
    """Run CrewAI multi-agent competitor analysis."""
    from pipelines.pipeline_4_competitor_analysis import run_competitor_pipeline
    result = run_competitor_pipeline()
    context["ti"].xcom_push(key="competitor_result", value=result)
    return result


with DAG(
    dag_id="echolab_competitor_analysis",
    default_args=default_args,
    description="CrewAI multi-agent competitor analysis (weekly)",
    schedule_interval="0 6 * * 1",  # Monday 6 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["echolab", "crewai", "competitor", "multi-agent", "pipeline-4"],
    max_active_runs=1,
) as dag:

    start = EmptyOperator(task_id="start")
    analyze = PythonOperator(task_id="competitor_analysis", python_callable=task_competitor_analysis)
    end = EmptyOperator(task_id="end")

    start >> analyze >> end
