"""Grain integrity assertions for analytics tables."""

from __future__ import annotations

import duckdb

from .config import GRAIN_DEFINITIONS, SCHEMA_ANALYTICS
from .db import close_connection, get_connection


def check_grain(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    key_columns: list[str],
    schema: str = SCHEMA_ANALYTICS,
) -> dict:
    """Assert that a table has the expected grain (unique key combination).

    Returns a dict with total rows, distinct key rows, and whether grain is valid.
    """
    key_expr = ", ".join(key_columns)
    result = conn.execute(f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT ({key_expr})) AS distinct_keys
        FROM {schema}.{table}
        """).fetchone()

    if not result:
        return {"table": table, "keys": key_columns, "valid": False, "error": "no data"}

    total, distinct = result
    valid = total == distinct

    return {
        "table": table,
        "keys": key_columns,
        "total_rows": total,
        "distinct_keys": distinct,
        "valid": valid,
    }


def check_all_grains(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """Run grain checks for all defined analytics tables."""
    results: list[dict] = []
    for table, keys in GRAIN_DEFINITIONS.items():
        if table_exists(conn, table, schema=SCHEMA_ANALYTICS):
            results.append(check_grain(conn, table, keys))
        else:
            results.append(
                {
                    "table": table,
                    "keys": keys,
                    "valid": False,
                    "error": "table not found",
                }
            )
    return results


def table_exists(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    schema: str = SCHEMA_ANALYTICS,
) -> bool:
    """Check whether a table exists in the given schema."""
    result = conn.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND table_name = '{table_name}'
        """).fetchone()
    return result[0] > 0 if result else False


def run_grain_checks(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> list[dict]:
    """Run all grain checks and return results."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        return check_all_grains(conn)
    finally:
        if close_conn:
            close_connection(conn)
