"""
=============================================================================
DAG 5: MONITORING, QUALITY AUDITING & REPORTING
=============================================================================
Schedule: Every 6 hours (trend detection + audit), Weekly (report)
Agents: trend_detector, quality_auditor, report_generator
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


def task_detect_trends(**context):
    from pipelines.pipeline_5_monitoring import detect_trends
    alerts = detect_trends()
    context["ti"].xcom_push(key="trend_alerts", value=alerts)
    return {"alerts": len(alerts)}


def task_audit_quality(**context):
    from pipelines.pipeline_5_monitoring import audit_model_quality
    report = audit_model_quality()
    context["ti"].xcom_push(key="quality_report", value=report)
    return report


def task_generate_report(**context):
    from pipelines.pipeline_5_monitoring import generate_report
    report = generate_report()
    context["ti"].xcom_push(key="weekly_report", value=report)
    return {"generated": True, "iterations": report.get("iterations", 0)}


with DAG(
    dag_id="echolab_monitoring",
    default_args=default_args,
    description="Trend detection, quality auditing, report generation (every 6h)",
    schedule_interval="0 */6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["echolab", "monitoring", "quality", "autogen", "pipeline-5"],
    max_active_runs=1,
) as dag:

    start = EmptyOperator(task_id="start")
    trends = PythonOperator(task_id="detect_trends", python_callable=task_detect_trends)
    audit = PythonOperator(task_id="audit_quality", python_callable=task_audit_quality)
    report = PythonOperator(task_id="generate_report", python_callable=task_generate_report)
    end = EmptyOperator(task_id="end")

    # Trends and audit run in parallel, then report
    start >> [trends, audit] >> report >> end
