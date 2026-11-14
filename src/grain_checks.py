"""Grain integrity assertions for analytics tables."""

from __future__ import annotations

from collections.abc import Iterable

import duckdb

from .config import GRAIN_DEFINITIONS, SCHEMA_ANALYTICS
from .db import close_connection, get_connection, table_exists


def check_grain(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    key_columns: list[str],
    schema: str = SCHEMA_ANALYTICS,
    allow_empty: bool = False,
) -> dict:
    """Assert that a table has the expected grain (unique key combination).

    Returns a dict with total rows, distinct key rows, duplicate/null-key counts,
    and whether the grain is valid. Mandatory tables must be non-empty unless
    allow_empty is explicitly True.
    """
    key_expr = ", ".join(key_columns)
    null_expr = " OR ".join(f"{col} IS NULL" for col in key_columns)
    result = conn.execute(f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT ({key_expr})) AS distinct_keys,
            SUM(CASE WHEN {null_expr} THEN 1 ELSE 0 END) AS null_key_rows
        FROM {schema}.{table}
        """).fetchone()

    if not result:
        return {
            "table": table,
            "keys": key_columns,
            "total_rows": 0,
            "distinct_keys": 0,
            "duplicate_key_rows": 0,
            "null_key_rows": 0,
            "valid": bool(allow_empty),
            "error": "no_data",
        }

    total, distinct, null_keys = result
    total_i = int(total or 0)
    distinct_i = int(distinct or 0)
    null_i = int(null_keys or 0)
    duplicate_rows = total_i - distinct_i
    valid = duplicate_rows == 0 and null_i == 0 and (allow_empty or total_i > 0)

    error = None
    if total_i == 0 and not allow_empty:
        error = "empty_table"
    elif null_i > 0:
        error = "null_keys"
    elif duplicate_rows > 0:
        error = "duplicate_keys"

    return {
        "table": table,
        "keys": key_columns,
        "total_rows": total_i,
        "distinct_keys": distinct_i,
        "duplicate_key_rows": duplicate_rows,
        "null_key_rows": null_i,
        "valid": valid,
        "error": error,
    }


def check_all_grains(
    conn: duckdb.DuckDBPyConnection,
    allowed_empty: Iterable[str] | None = None,
) -> list[dict]:
    """Run grain checks for all defined analytics tables."""
    allowed = set(allowed_empty or [])
    results: list[dict] = []
    for table, keys in GRAIN_DEFINITIONS.items():
        if table_exists(conn, table, schema=SCHEMA_ANALYTICS):
            results.append(check_grain(conn, table, keys, allow_empty=table in allowed))
        else:
            results.append(
                {
                    "table": table,
                    "keys": keys,
                    "total_rows": 0,
                    "distinct_keys": 0,
                    "duplicate_key_rows": 0,
                    "null_key_rows": 0,
                    "valid": False,
                    "error": "table_not_found",
                }
            )
    return results


def run_grain_checks(
    conn: duckdb.DuckDBPyConnection | None = None,
    allowed_empty: Iterable[str] | None = None,
) -> list[dict]:
    """Run all grain checks and return results."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        return check_all_grains(conn, allowed_empty=allowed_empty)
    finally:
        if close_conn:
            close_connection(conn)
