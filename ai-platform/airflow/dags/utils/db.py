"""
=============================================================================
DATABASE UTILITIES FOR AIRFLOW DAGS
=============================================================================
Shared database connection utilities used across all 5 pipelines.

INTERVIEW TIP: Connection pooling is critical for production. Without it,
each task would create/destroy connections, causing PostgreSQL to run out
of connections under load (50k+ queries/day).
=============================================================================
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager

POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "echolab"),
    "user": os.getenv("POSTGRES_USER", "echolab"),
    "password": os.getenv("POSTGRES_PASSWORD", "echolab_secret_2024"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic cleanup."""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Execute a query and return all results as dicts."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute_query(query, params=None):
    """Execute a write query (INSERT, UPDATE, DELETE)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


def bulk_insert(table, columns, values):
    """Bulk insert using execute_values for high throughput."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cols = ", ".join(columns)
            query = f"INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
            execute_values(cur, query, values)
            return cur.rowcount
