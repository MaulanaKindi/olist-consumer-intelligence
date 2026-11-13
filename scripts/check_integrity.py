import json
from pathlib import Path

import duckdb

DB_PATH = "db/olist.duckdb"


def check_integrity():
    conn = duckdb.connect(DB_PATH, read_only=True)
    results = {}

    checks = {
        "order_items_to_orders": "SELECT count(*) FROM raw.order_items WHERE order_id NOT IN (SELECT order_id FROM raw.orders)",
        "order_items_to_products": "SELECT count(*) FROM raw.order_items WHERE product_id NOT IN (SELECT product_id FROM raw.products)",
        "order_items_to_sellers": "SELECT count(*) FROM raw.order_items WHERE seller_id NOT IN (SELECT seller_id FROM raw.sellers)",
        "payments_to_orders": "SELECT count(*) FROM raw.payments WHERE order_id NOT IN (SELECT order_id FROM raw.orders)",
        "reviews_to_orders": "SELECT count(*) FROM raw.reviews WHERE order_id NOT IN (SELECT order_id FROM raw.orders)",
        "orders_to_customers": "SELECT count(*) FROM raw.orders WHERE customer_id NOT IN (SELECT customer_id FROM raw.customers)",
    }

    for name, sql in checks.items():
        count = conn.execute(sql).fetchone()[0]
        results[name] = {"orphaned_count": count, "status": "PASS" if count == 0 else "FAIL"}

    # Custom checks
    # Geolocation deduplication check
    results["geolocation_uniqueness"] = {
        "total_rows": conn.execute("SELECT count(*) FROM raw.geolocation").fetchone()[0],
        "distinct_zip_prefixes": conn.execute(
            "SELECT count(DISTINCT geolocation_zip_code_prefix) FROM raw.geolocation"
        ).fetchone()[0],
    }

    # Output results
    output_path = Path("docs/olist/integrity_check.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Referential integrity check completed. Results saved to {output_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    check_integrity()
