"""Validate analytics tables: grain integrity and transformation correctness."""

import json
from pathlib import Path

import duckdb

DB_PATH = "db/olist.duckdb"
OUT = Path("docs/olist/analytics_validation.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

GRAIN_DEFINITIONS = {
    "fact_orders": ["order_id"],
    "fact_order_items": ["order_id", "order_item_id"],
    "dim_customers": ["customer_unique_id"],
    "dim_products": ["product_id"],
    "dim_sellers": ["seller_id"],
    "fact_payments": ["order_id", "payment_sequential"],
    "fact_reviews": ["review_id"],
    "fact_delivery": ["order_id"],
}

results = {"grain": [], "transforms": []}

conn = duckdb.connect(DB_PATH, read_only=True)

# 1. Grain checks
for table, keys in GRAIN_DEFINITIONS.items():
    key_expr = ", ".join(keys)
    total, distinct = conn.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT ({key_expr})) FROM analytics.{table}"
    ).fetchone()
    results["grain"].append(
        {
            "table": table,
            "keys": keys,
            "total_rows": total,
            "distinct_keys": distinct,
            "valid": total == distinct,
        }
    )

# 2. Transformation correctness checks
# fact_orders: order_total_value should equal sum of payments per order
mismatch = conn.execute("""
    SELECT COUNT(*) FROM analytics.fact_orders fo
    WHERE ABS(fo.order_total_value - (
        SELECT SUM(p.payment_value) FROM staging.payments p WHERE p.order_id = fo.order_id
    )) > 0.01
""").fetchone()[0]
results["transforms"].append(
    {
        "check": "fact_orders.order_total_value == sum(payments)",
        "mismatches": mismatch,
        "valid": mismatch == 0,
    }
)

# fact_orders: order_items_count should equal count of order_items
mismatch = conn.execute("""
    SELECT COUNT(*) FROM analytics.fact_orders fo
    WHERE fo.order_items_count != (
        SELECT COUNT(*) FROM staging.order_items oi WHERE oi.order_id = fo.order_id
    )
""").fetchone()[0]
results["transforms"].append(
    {
        "check": "fact_orders.order_items_count == count(order_items)",
        "mismatches": mismatch,
        "valid": mismatch == 0,
    }
)

# fact_order_items: grain should be unique per (order_id, order_item_id)
total, distinct = conn.execute(
    "SELECT COUNT(*), COUNT(DISTINCT (order_id, order_item_id)) FROM analytics.fact_order_items"
).fetchone()
results["transforms"].append(
    {
        "check": "fact_order_items grain unique",
        "total_rows": total,
        "distinct_keys": distinct,
        "valid": total == distinct,
    }
)

# fact_reviews: review_score should be 1-5
invalid = conn.execute(
    "SELECT COUNT(*) FROM analytics.fact_reviews WHERE valid_review_score IS NULL AND review_score IS NOT NULL"
).fetchone()[0]
results["transforms"].append(
    {
        "check": "fact_reviews review_score in 1-5",
        "invalid_scores": invalid,
        "valid": invalid == 0,
    }
)

# dim_customers: total_orders should match count of orders per customer
mismatch = conn.execute("""
    SELECT COUNT(*) FROM analytics.dim_customers dc
    WHERE dc.total_orders != (
        SELECT COUNT(*) FROM staging.orders o WHERE o.customer_id = dc.customer_id
    )
""").fetchone()[0]
results["transforms"].append(
    {
        "check": "dim_customers.total_orders == count(orders)",
        "mismatches": mismatch,
        "valid": mismatch == 0,
    }
)

# fact_delivery: delivery_time_days should match fact_orders
mismatch = conn.execute("""
    SELECT COUNT(*) FROM analytics.fact_delivery fd
    JOIN analytics.fact_orders fo ON fd.order_id = fo.order_id
    WHERE fd.delivery_time_days IS DISTINCT FROM fo.delivery_time_days
""").fetchone()[0]
results["transforms"].append(
    {
        "check": "fact_delivery.delivery_time_days == fact_orders.delivery_time_days",
        "mismatches": mismatch,
        "valid": mismatch == 0,
    }
)

conn.close()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(json.dumps(results, indent=2))
print(f"\nValidation results saved to {OUT}")
