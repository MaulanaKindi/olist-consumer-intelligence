"""Referential integrity checks for raw Olist tables."""

import argparse
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import DUCKDB_PATH, PROJECT_ROOT  # noqa: E402


def check_integrity(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=str(DUCKDB_PATH))
    parser.add_argument(
        "--out",
        type=str,
        default=str(PROJECT_ROOT / "docs" / "olist" / "integrity_check.json"),
    )
    args = parser.parse_args(argv)

    db_path = Path(args.db_path)
    output_path = Path(args.out)
    conn = duckdb.connect(str(db_path), read_only=True)
    results = {}
    try:
        checks = [
            ("order_items_to_orders", "raw.order_items", "order_id", "raw.orders", "order_id"),
            (
                "order_items_to_products",
                "raw.order_items",
                "product_id",
                "raw.products",
                "product_id",
            ),
            (
                "order_items_to_sellers",
                "raw.order_items",
                "seller_id",
                "raw.sellers",
                "seller_id",
            ),
            ("payments_to_orders", "raw.payments", "order_id", "raw.orders", "order_id"),
            ("reviews_to_orders", "raw.reviews", "order_id", "raw.orders", "order_id"),
            (
                "orders_to_customers",
                "raw.orders",
                "customer_id",
                "raw.customers",
                "customer_id",
            ),
        ]

        for name, child, child_col, parent, parent_col in checks:
            total, null_fk, orphaned = conn.execute(f"""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN c.{child_col} IS NULL THEN 1 ELSE 0 END) AS null_fk,
                    SUM(
                        CASE
                            WHEN c.{child_col} IS NOT NULL
                             AND NOT EXISTS (
                                 SELECT 1 FROM {parent} p
                                 WHERE p.{parent_col} = c.{child_col}
                             )
                            THEN 1 ELSE 0
                        END
                    ) AS orphaned
                FROM {child} c
                """).fetchone()
            total_i = int(total or 0)
            null_i = int(null_fk or 0)
            orphaned_i = int(orphaned or 0)
            comparable = total_i - null_i
            integrity_rate = 1.0 - (orphaned_i / comparable) if comparable > 0 else 1.0
            status = "PASS" if orphaned_i == 0 else "FAIL"
            results[name] = {
                "total_rows": total_i,
                "null_fk_rows": null_i,
                "orphaned_count": orphaned_i,
                "integrity_rate": integrity_rate,
                "status": status,
            }

        total_geo, distinct_zip = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT geolocation_zip_code_prefix) FROM raw.geolocation"
        ).fetchone()
        results["geolocation_uniqueness"] = {
            "total_rows": int(total_geo),
            "distinct_zip_prefixes": int(distinct_zip),
            "note": "Multiple rows per zip prefix are expected in source; staging deduplicates per prefix.",
        }
    finally:
        conn.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=4), encoding="utf-8")

    print(f"Referential integrity check completed. Results saved to {output_path}")
    print(json.dumps(results, indent=2))

    failed = [k for k, v in results.items() if isinstance(v, dict) and v.get("status") == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(check_integrity())
