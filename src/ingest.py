"""Data ingestion module: load raw Olist CSV files into DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb

from .config import RAW_DATA_DIR, SCHEMA_RAW, SOURCE_FILES
from .db import close_connection, get_connection, table_exists


def ingest_one(
    conn: duckdb.DuckDBPyConnection,
    csv_path: Path,
    table_name: str,
    schema: str = SCHEMA_RAW,
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
    if not csv_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")

    full_table = f"{schema}.{table_name}"
    exists = table_exists(conn, table_name, schema)

    if exists and not overwrite:
        raise ValueError(f"Table {full_table} already exists. Use overwrite=True to replace it.")

    conn.execute(f"""
        CREATE OR REPLACE TABLE {full_table} AS
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
        If True, replace existing raw tables. If False, fail when any expected
        raw table already exists (explicit, non-destructive rerun behavior).

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
        missing_files = [
            key for key, filename in SOURCE_FILES.items() if not (dir_path / filename).exists()
        ]
        if missing_files:
            missing_names = [SOURCE_FILES[k] for k in missing_files]
            raise FileNotFoundError(f"Missing required source files in {dir_path}: {missing_names}")

        existing = [key for key in SOURCE_FILES if table_exists(conn, key, SCHEMA_RAW)]
        if existing and not overwrite:
            raise ValueError(
                "Raw tables already exist "
                f"({existing}). Re-run with overwrite=True for a full rebuild, "
                "or run downstream stages (validate/transform/grain-checks)."
            )

        for key, filename in SOURCE_FILES.items():
            csv_path = dir_path / filename
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
