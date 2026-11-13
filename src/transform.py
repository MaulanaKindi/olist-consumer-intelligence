"""ETL transformation module: build staging and analytics tables from raw data."""

from __future__ import annotations

from pathlib import Path

import duckdb

from .config import (
    QUERIES_DIR,
    SCHEMA_ANALYTICS,
    SCHEMA_RAW,
    SCHEMA_STAGING,
)
from .db import close_connection, get_connection


def _run_sql_file(conn: duckdb.DuckDBPyConnection, sql_path: Path) -> None:
    """Execute a SQL file against the connection."""
    sql = sql_path.read_text(encoding="utf-8")
    conn.execute(sql)


def build_staging(conn: duckdb.DuckDBPyConnection) -> None:
    """Create staging tables from raw data with basic cleaning."""
    staging_sql = QUERIES_DIR / "01_staging.sql"
    if staging_sql.exists():
        _run_sql_file(conn, staging_sql)
    else:
        # Fallback: create minimal staging tables as SELECT * from raw
        for table in [
            "orders",
            "order_items",
            "customers",
            "products",
            "sellers",
            "payments",
            "reviews",
            "geolocation",
            "category_translation",
        ]:
            conn.execute(
                f"CREATE OR REPLACE TABLE {SCHEMA_STAGING}.{table} AS "
                f"SELECT * FROM {SCHEMA_RAW}.{table}"
            )


def build_analytics(conn: duckdb.DuckDBPyConnection) -> None:
    """Create analytics fact and dimension tables from staging data."""
    analytics_sql = QUERIES_DIR / "02_analytics.sql"
    if analytics_sql.exists():
        _run_sql_file(conn, analytics_sql)
    else:
        # Minimal fallback: copy staging to analytics
        for table in [
            "orders",
            "order_items",
            "customers",
            "products",
            "sellers",
            "payments",
            "reviews",
            "geolocation",
            "category_translation",
        ]:
            conn.execute(
                f"CREATE OR REPLACE TABLE {SCHEMA_ANALYTICS}.{table} AS "
                f"SELECT * FROM {SCHEMA_STAGING}.{table}"
            )


def transform_all(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> None:
    """Run the full ETL transformation: raw -> staging -> analytics."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        print("Building staging tables...")
        build_staging(conn)
        print("Staging tables built.")

        print("Building analytics tables...")
        build_analytics(conn)
        print("Analytics tables built.")
    finally:
        if close_conn:
            close_connection(conn)
