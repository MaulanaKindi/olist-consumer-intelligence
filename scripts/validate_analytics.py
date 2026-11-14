"""Validate analytics tables: grain integrity and transformation correctness."""

import argparse
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DUCKDB_PATH, GRAIN_DEFINITIONS, PROJECT_ROOT  # noqa: E402

DEFAULT_OUT = PROJECT_ROOT / "docs" / "olist" / "analytics_validation.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=str(DUCKDB_PATH))
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    db_path = Path(args.db_path)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = {"grain": [], "transforms": []}
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        # 1. Grain checks (must be non-empty and have unique, non-null keys)
        for table, keys in GRAIN_DEFINITIONS.items():
            key_expr = ", ".join(keys)
            null_expr = " OR ".join(f"{k} IS NULL" for k in keys)
            total, distinct, null_keys = conn.execute(f"""
                SELECT
                    COUNT(*),
                    COUNT(DISTINCT ({key_expr})),
                    SUM(CASE WHEN {null_expr} THEN 1 ELSE 0 END)
                FROM analytics.{table}
                """).fetchone()
            total_i, distinct_i, null_i = int(total), int(distinct), int(null_keys or 0)
            valid = total_i > 0 and total_i == distinct_i and null_i == 0
            results["grain"].append(
                {
                    "table": table,
                    "keys": keys,
                    "total_rows": total_i,
                    "distinct_keys": distinct_i,
                    "null_key_rows": null_i,
                    "valid": valid,
                }
            )

        # 2. Transformation correctness checks
        mismatch = conn.execute("""
            SELECT COUNT(*) FROM analytics.fact_orders fo
            WHERE ABS(COALESCE(fo.order_total_value, 0) - COALESCE((
                SELECT SUM(p.payment_value) FROM staging.payments p
                WHERE p.order_id = fo.order_id
            ), 0)) > 0.01
            """).fetchone()[0]
        results["transforms"].append(
            {
                "check": "fact_orders.order_total_value == sum(payments)",
                "mismatches": int(mismatch),
                "valid": int(mismatch) == 0,
            }
        )

        mismatch = conn.execute("""
            SELECT COUNT(*) FROM analytics.fact_orders fo
            WHERE fo.order_items_count != COALESCE((
                SELECT COUNT(*) FROM staging.order_items oi WHERE oi.order_id = fo.order_id
            ), 0)
            """).fetchone()[0]
        results["transforms"].append(
            {
                "check": "fact_orders.order_items_count == count(order_items)",
                "mismatches": int(mismatch),
                "valid": int(mismatch) == 0,
            }
        )

        total, distinct = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT (order_id, order_item_id)) FROM analytics.fact_order_items"
        ).fetchone()
        results["transforms"].append(
            {
                "check": "fact_order_items grain unique",
                "total_rows": int(total),
                "distinct_keys": int(distinct),
                "valid": int(total) == int(distinct) and int(total) > 0,
            }
        )

        bad_flag = conn.execute("""
            SELECT COUNT(*) FROM analytics.fact_reviews
            WHERE (valid_review_score IS NULL AND TRY_CAST(review_score AS INTEGER) BETWEEN 1 AND 5)
               OR (valid_review_score IS NOT NULL AND valid_review_score NOT BETWEEN 1 AND 5)
            """).fetchone()[0]
        results["transforms"].append(
            {
                "check": "fact_reviews valid_review_score consistent with 1-5 range",
                "invalid_scores": int(bad_flag),
                "valid": int(bad_flag) == 0,
            }
        )

        mismatch = conn.execute("""
            WITH cust_orders AS (
                SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS expected_orders
                FROM staging.customers c
                JOIN staging.orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_unique_id
            )
            SELECT COUNT(*)
            FROM analytics.dim_customers dc
            LEFT JOIN cust_orders co ON dc.customer_unique_id = co.customer_unique_id
            WHERE dc.total_orders != COALESCE(co.expected_orders, 0)
            """).fetchone()[0]
        results["transforms"].append(
            {
                "check": "dim_customers.total_orders == distinct orders per customer_unique_id",
                "mismatches": int(mismatch),
                "valid": int(mismatch) == 0,
            }
        )

        mismatch = conn.execute("""
            SELECT COUNT(*) FROM analytics.fact_delivery fd
            JOIN analytics.fact_orders fo ON fd.order_id = fo.order_id
            WHERE fd.delivery_time_days IS DISTINCT FROM fo.delivery_time_days
            """).fetchone()[0]
        results["transforms"].append(
            {
                "check": "fact_delivery.delivery_time_days == fact_orders.delivery_time_days",
                "mismatches": int(mismatch),
                "valid": int(mismatch) == 0,
            }
        )

        geo_coverage = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM staging.orders) AS staging_orders,
                (SELECT COUNT(*) FROM staging.orders o JOIN staging.customers c ON o.customer_id=c.customer_id) AS mapped_orders,
                (SELECT COUNT(*) FROM analytics.fact_orders) AS fact_orders
            """).fetchone()
        stg, mapped, fact = [int(x) for x in geo_coverage]
        results["transforms"].append(
            {
                "check": "geographic order mapping coverage via staging.customers.customer_id",
                "staging_orders": stg,
                "mapped_orders": mapped,
                "fact_orders": fact,
                "valid": stg == mapped == fact,
            }
        )

        for dim, key in [("dim_products", "product_id"), ("dim_sellers", "seller_id")]:
            mismatch = conn.execute(f"""
                WITH expected AS (
                    SELECT {key}, COUNT(*) AS n FROM staging.order_items GROUP BY {key}
                )
                SELECT COUNT(*)
                FROM analytics.{dim} d
                LEFT JOIN expected e ON d.{key} = e.{key}
                WHERE d.total_items_sold != COALESCE(e.n, 0)
                """).fetchone()[0]
            results["transforms"].append(
                {
                    "check": f"{dim}.total_items_sold == count(order_items) by {key}",
                    "mismatches": int(mismatch),
                    "valid": int(mismatch) == 0,
                }
            )

        ok = all(r.get("valid") for r in results["grain"]) and all(
            r.get("valid") for r in results["transforms"]
        )
    finally:
        conn.close()

    out_path.write_text(json.dumps(results, indent=4), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"\nValidation results saved to {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
