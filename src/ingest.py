"""Data ingestion module: load raw Olist CSV files into DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb

from .config import RAW_DATA_DIR, SOURCE_FILES
from .db import close_connection, get_connection, table_exists


def ingest_one(
    conn: duckdb.DuckDBPyConnection,
    csv_path: Path,
    table_name: str,
    schema: str = "raw",
    overwrite: bool = False,
) -> int:
    """Load a single CSV file into a DuckDB table.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    csv_path : Path
        Path to the source CSV file.
    table_name : str
        Target table name (without schema prefix).
    schema : str, default "raw"
        Target schema name.
    overwrite : bool, default False
        If True, drop and recreate the table before loading.

    Returns
    -------
    int
        Number of rows loaded.
    """
    full_table = f"{schema}.{table_name}"

    if overwrite and table_exists(conn, table_name, schema):
        conn.execute(f"DROP TABLE IF EXISTS {full_table};")

    if table_exists(conn, table_name, schema):
        raise ValueError(f"Table {full_table} already exists. Use overwrite=True to replace it.")

    conn.execute(f"""
        CREATE TABLE {full_table} AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)
        """)

    count_row = conn.execute(f"SELECT COUNT(*) FROM {full_table}").fetchone()
    count = count_row[0] if count_row else 0
    return int(count)


def ingest_all(
    conn: duckdb.DuckDBPyConnection | None = None,
    data_dir: Path | None = None,
    overwrite: bool = False,
) -> dict[str, int]:
    """Load all expected Olist CSV files into the raw schema.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection, optional
        Open DuckDB connection. If None, a new connection is opened and closed.
    data_dir : Path, optional
        Directory containing raw CSV files. Defaults to config.RAW_DATA_DIR.
    overwrite : bool, default False
        If True, drop and recreate tables before loading.

    Returns
    -------
    dict[str, int]
        Mapping of table name to row count loaded.
    """
    dir_path = data_dir or RAW_DATA_DIR
    dir_path.mkdir(parents=True, exist_ok=True)

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    results: dict[str, int] = {}

    try:
        for key, filename in SOURCE_FILES.items():
            csv_path = dir_path / filename
            if not csv_path.exists():
                print(f"Warning: {csv_path} not found, skipping.")
                continue

            rows = ingest_one(conn, csv_path, key, overwrite=overwrite)
            results[key] = rows
            print(f"Loaded {key}: {rows:,} rows from {filename}")
    finally:
        if close_conn:
            close_connection(conn)

    return results


def list_source_files(data_dir: Path | None = None) -> dict[str, bool]:
    """Check which expected source files are present.

    Parameters
    ----------
    data_dir : Path, optional
        Directory to check. Defaults to config.RAW_DATA_DIR.

    Returns
    -------
    dict[str, bool]
        Mapping of table name to whether the file exists.
    """
    dir_path = data_dir or RAW_DATA_DIR
    return {key: (dir_path / filename).exists() for key, filename in SOURCE_FILES.items()}
