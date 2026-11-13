"""DuckDB connection helpers for the Olist intelligence pipeline."""

from __future__ import annotations

from pathlib import Path

import duckdb

from .config import DUCKDB_PATH, SCHEMA_ANALYTICS, SCHEMA_RAW, SCHEMA_STAGING


def get_connection(
    db_path: Path | None = None,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    """Open (or create) a DuckDB connection and ensure schemas exist.

    Parameters
    ----------
    db_path : Path, optional
        Path to the DuckDB database file. Defaults to config.DUCKDB_PATH.
    read_only : bool, default False
        Open the database in read-only mode when True.

    Returns
    -------
    duckdb.DuckDBPyConnection
        An open DuckDB connection with raw, staging, and analytics schemas.
    """
    path = db_path or DUCKDB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(path), read_only=read_only)

    # Ensure schemas exist
    if not read_only:
        for schema in (SCHEMA_RAW, SCHEMA_STAGING, SCHEMA_ANALYTICS):
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

    return conn


def close_connection(conn: duckdb.DuckDBPyConnection) -> None:
    """Safely close a DuckDB connection."""
    try:
        conn.close()
    except Exception:
        pass


def table_exists(
    conn: duckdb.DuckDBPyConnection, table_name: str, schema: str = SCHEMA_RAW
) -> bool:
    """Check whether a table exists in the given schema."""
    result = conn.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND table_name = '{table_name}'
        """).fetchone()
    return result[0] > 0 if result else False


def list_tables(conn: duckdb.DuckDBPyConnection, schema: str = SCHEMA_RAW) -> list[str]:
    """List all tables in the given schema."""
    result = conn.execute(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
        ORDER BY table_name
        """).fetchall()
    return [row[0] for row in result]


def row_count(conn: duckdb.DuckDBPyConnection, table_name: str, schema: str = SCHEMA_RAW) -> int:
    """Return the row count of a table."""
    result = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}").fetchone()
    return result[0] if result else 0
