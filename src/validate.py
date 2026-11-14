"""Data validation and quality checks for Olist datasets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from .config import FINDINGS_DIR, REVIEW_SCORE_MAX, REVIEW_SCORE_MIN, SCHEMA_RAW
from .db import row_count, table_exists


def check_row_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return row counts for all raw tables."""
    counts: dict[str, int] = {}
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
        if table_exists(conn, table, schema=SCHEMA_RAW):
            counts[table] = row_count(conn, table, schema=SCHEMA_RAW)
    return counts


def check_null_rates(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: list[str],
    schema: str = SCHEMA_RAW,
) -> dict[str, float]:
    """Return null rate (0-1) for each column in a table."""
    rates: dict[str, float] = {}
    for col in columns:
        result = conn.execute(f"""
            SELECT
                COUNT(*) AS total,
                COUNT({col}) AS non_null
            FROM {schema}.{table}
            """).fetchone()
        total, non_null = result if result else (0, 0)
        rates[col] = 1.0 - (non_null / total) if total > 0 else 0.0
    return rates


def check_primary_key_uniqueness(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    key_columns: list[str],
    schema: str = SCHEMA_RAW,
) -> bool:
    """Check that key columns are unique and non-null in a table."""
    key_expr = ", ".join(key_columns)
    null_expr = " OR ".join(f"{col} IS NULL" for col in key_columns)
    result = conn.execute(f"""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT ({key_expr})) AS distinct_keys,
            SUM(CASE WHEN {null_expr} THEN 1 ELSE 0 END) AS null_keys
        FROM {schema}.{table}
        """).fetchone()
    if not result:
        return False
    total, distinct, null_keys = result
    return bool(total == distinct and int(null_keys or 0) == 0 and int(total or 0) > 0)


def check_referential_integrity(
    conn: duckdb.DuckDBPyConnection,
    child_table: str,
    child_column: str,
    parent_table: str,
    parent_column: str,
    child_schema: str = SCHEMA_RAW,
    parent_schema: str = SCHEMA_RAW,
) -> dict[str, int | float]:
    """Check referential integrity between two tables.

    Returns dict with total child rows, null FK rows, orphaned non-null rows,
    and integrity rate over non-null FK rows.
    """
    result = conn.execute(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN c.{child_column} IS NULL THEN 1 ELSE 0 END) AS null_fk,
            SUM(
                CASE
                    WHEN c.{child_column} IS NOT NULL
                     AND NOT EXISTS (
                         SELECT 1
                         FROM {parent_schema}.{parent_table} p
                         WHERE p.{parent_column} = c.{child_column}
                     )
                    THEN 1 ELSE 0
                END
            ) AS orphaned
        FROM {child_schema}.{child_table} c
        """).fetchone()
    if not result:
        return {"total": 0, "null_fk": 0, "orphaned": 0, "integrity_rate": 1.0}
    total, null_fk, orphaned = result
    total_i = int(total or 0)
    null_i = int(null_fk or 0)
    orphaned_i = int(orphaned or 0)
    comparable = total_i - null_i
    rate = 1.0 - (float(orphaned_i) / float(comparable)) if comparable > 0 else 1.0
    return {
        "total": total_i,
        "null_fk": null_i,
        "orphaned": orphaned_i,
        "integrity_rate": rate,
    }


def check_date_range(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    date_column: str,
    schema: str = SCHEMA_RAW,
) -> dict[str, str]:
    """Return min and max dates for a date column."""
    result = conn.execute(f"""
        SELECT MIN({date_column}), MAX({date_column})
        FROM {schema}.{table}
        """).fetchone()
    if not result or result[0] is None:
        return {"min": "", "max": ""}
    return {"min": str(result[0]), "max": str(result[1])}


def check_review_score_range(
    conn: duckdb.DuckDBPyConnection,
    table: str = "reviews",
    score_column: str = "review_score",
    schema: str = SCHEMA_RAW,
) -> dict[str, int | float]:
    """Check that review scores are present, numeric-castable, and within range (1-5)."""
    result = conn.execute(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN {score_column} IS NULL THEN 1 ELSE 0 END) AS null_count,
            SUM(
                CASE
                    WHEN {score_column} IS NOT NULL
                     AND TRY_CAST({score_column} AS INTEGER) IS NULL
                    THEN 1 ELSE 0
                END
            ) AS non_numeric,
            SUM(
                CASE
                    WHEN TRY_CAST({score_column} AS INTEGER) IS NOT NULL
                     AND (
                         CAST(TRY_CAST({score_column} AS INTEGER) AS INTEGER) < {REVIEW_SCORE_MIN}
                      OR CAST(TRY_CAST({score_column} AS INTEGER) AS INTEGER) > {REVIEW_SCORE_MAX}
                     )
                    THEN 1 ELSE 0
                END
            ) AS out_of_range,
            SUM(
                CASE
                    WHEN TRY_CAST({score_column} AS INTEGER) IS NOT NULL
                     AND CAST(TRY_CAST({score_column} AS INTEGER) AS INTEGER)
                         BETWEEN {REVIEW_SCORE_MIN} AND {REVIEW_SCORE_MAX}
                    THEN 1 ELSE 0
                END
            ) AS valid
        FROM {schema}.{table}
        """).fetchone()
    if not result:
        return {
            "total": 0,
            "null": 0,
            "non_numeric": 0,
            "out_of_range": 0,
            "invalid": 0,
            "valid": 0,
            "valid_rate": 1.0,
        }
    total, null_count, non_numeric, out_of_range, valid = result
    total_i = int(total or 0)
    null_i = int(null_count or 0)
    non_num_i = int(non_numeric or 0)
    oor_i = int(out_of_range or 0)
    valid_i = int(valid or 0)
    invalid_i = null_i + non_num_i + oor_i
    rate = (float(valid_i) / float(total_i)) if total_i > 0 else 1.0
    return {
        "total": total_i,
        "null": null_i,
        "non_numeric": non_num_i,
        "out_of_range": oor_i,
        "invalid": invalid_i,
        "valid": valid_i,
        "valid_rate": rate,
    }


def run_all_checks(conn: duckdb.DuckDBPyConnection) -> dict:
    """Run all validation checks and return a results dictionary."""
    results: dict = {
        "row_counts": check_row_counts(conn),
        "null_rates": {},
        "primary_key_uniqueness": {},
        "referential_integrity": {},
        "date_ranges": {},
        "review_score_range": {},
    }

    null_checks = {
        "orders": ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
        "order_items": ["order_id", "order_item_id", "product_id", "seller_id"],
        "customers": ["customer_id", "customer_unique_id"],
        "products": ["product_id", "product_category_name"],
        "sellers": ["seller_id"],
        "payments": ["order_id", "payment_sequential", "payment_type", "payment_value"],
        "reviews": ["review_id", "order_id", "review_score"],
        "geolocation": ["geolocation_zip_code_prefix"],
    }
    for table, columns in null_checks.items():
        if table_exists(conn, table, schema=SCHEMA_RAW):
            results["null_rates"][table] = check_null_rates(conn, table, columns, schema=SCHEMA_RAW)

    pk_checks = {
        "orders": ["order_id"],
        "order_items": ["order_id", "order_item_id"],
        "customers": ["customer_id"],
        "products": ["product_id"],
        "sellers": ["seller_id"],
        "reviews": ["review_id"],
    }
    for table, keys in pk_checks.items():
        if table_exists(conn, table, schema=SCHEMA_RAW):
            results["primary_key_uniqueness"][table] = check_primary_key_uniqueness(
                conn, table, keys, schema=SCHEMA_RAW
            )

    ri_checks = [
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("order_items", "seller_id", "sellers", "seller_id"),
        ("payments", "order_id", "orders", "order_id"),
        ("reviews", "order_id", "orders", "order_id"),
    ]
    for child, child_col, parent, parent_col in ri_checks:
        if table_exists(conn, child, schema=SCHEMA_RAW) and table_exists(
            conn, parent, schema=SCHEMA_RAW
        ):
            key = f"{child}.{child_col} -> {parent}.{parent_col}"
            results["referential_integrity"][key] = check_referential_integrity(
                conn, child, child_col, parent, parent_col
            )

    date_checks = {"orders": "order_purchase_timestamp"}
    for table, col in date_checks.items():
        if table_exists(conn, table, schema=SCHEMA_RAW):
            results["date_ranges"][table] = check_date_range(conn, table, col, schema=SCHEMA_RAW)

    if table_exists(conn, "reviews", schema=SCHEMA_RAW):
        results["review_score_range"] = check_review_score_range(conn)

    return results


def save_findings(results: dict, output_path: Path | None = None) -> Path:
    """Save validation results as JSON."""
    path = output_path or (FINDINGS_DIR / "data_quality.json")
    path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "results": results,
    }

    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path
