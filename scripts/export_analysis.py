import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB = "db/olist.duckdb"
OUT_F = Path("outputs/findings")
OUT_F.mkdir(parents=True, exist_ok=True)
OUT_C = Path("outputs/charts")
OUT_C.mkdir(parents=True, exist_ok=True)
OUT_R = Path("outputs/reports")
OUT_R.mkdir(parents=True, exist_ok=True)

conn = duckdb.connect(DB, read_only=True)


def q(sql):
    return conn.execute(sql).fetchdf()


findings = {
    "kpi_governance": {
        "source": "docs/olist/03_kpi_definitions.md",
        "version": "1.1",
        "status_filter_default": "all order_status",
    }
}

dq = json.loads(Path("outputs/findings/data_quality.json").read_text(encoding="utf-8"))
findings["data_quality"] = dq["results"]

orders = q("""
SELECT
  COUNT(DISTINCT order_id) AS order_count,
  SUM(order_total_value) AS gmv_payments,
  AVG(order_total_value) AS aov,
  quantile_cont(order_total_value, 0.5) AS median_order_value,
  AVG(order_items_count) AS avg_items_per_order
FROM analytics.fact_orders
""").iloc[0].to_dict()

repeat = q("""
WITH orders_per AS (
  SELECT cu.customer_unique_id, COUNT(DISTINCT o.order_id) AS cnt
  FROM staging.orders o
  JOIN staging.customers cu ON o.customer_id = cu.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT COUNT(*) AS customers,
       SUM(CASE WHEN cnt > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       AVG(cnt) AS avg_orders_per_customer
FROM orders_per
""").iloc[0].to_dict()
repeat["repeat_customer_rate"] = (
    (float(repeat["repeat_customers"]) / float(repeat["customers"]))
    if repeat["customers"]
    else None
)

cancel = q("""
SELECT
  COUNT(*) AS orders_all,
  SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS canceled_orders
FROM analytics.fact_orders
""").iloc[0].to_dict()
cancel["cancellation_rate"] = (
    (float(cancel["canceled_orders"]) / float(cancel["orders_all"]))
    if cancel["orders_all"]
    else None
)

status = q("""
SELECT order_status, COUNT(*) AS order_count
FROM analytics.fact_orders
GROUP BY order_status
ORDER BY order_count DESC
""").to_dict(orient="records")

monthly = q("""
SELECT strftime(order_purchase_timestamp, '%Y-%m') AS month,
       COUNT(DISTINCT order_id) AS order_count,
       SUM(order_total_value) AS gmv_payments
FROM analytics.fact_orders
GROUP BY 1 ORDER BY 1
""")
monthly.to_csv(OUT_F / "monthly_orders.csv", index=False)

findings["consumer_behavior"] = {
    "grain": "order (fact_orders), customer_unique_id (staging.customers+orders for repeat)",
    "order_status_filter": "all",
    "kpis": {**orders, **repeat, **cancel},
    "order_status_distribution": status,
}

plt.figure(figsize=(10, 4))
plt.plot(monthly["month"], monthly["order_count"], marker="o")
plt.xticks(rotation=45, ha="right")
plt.title("Monthly Order Count (all statuses)")
plt.ylabel("Orders")
plt.tight_layout()
plt.savefig(OUT_C / "monthly_orders.png", dpi=150)
plt.close()

review_kpi = q("""
SELECT AVG(valid_review_score) AS avg_review_score,
       COUNT(*) AS reviews_valid
FROM analytics.fact_reviews
WHERE valid_review_score IS NOT NULL
""").iloc[0].to_dict()

delivery_kpi = q("""
SELECT
  AVG(CASE WHEN is_delivered AND delivery_time_days IS NOT NULL THEN delivery_time_days END) AS avg_delivery_days,
  SUM(CASE WHEN is_delivered AND delivery_time_days IS NOT NULL THEN 1 ELSE 0 END) AS delivered_orders_with_days,
  SUM(CASE WHEN is_delivered AND delivery_gap_days IS NOT NULL AND delivery_gap_days >= 0 THEN 1 ELSE 0 END) AS on_time_or_early_orders,
  SUM(CASE WHEN is_delivered AND delivery_gap_days IS NOT NULL THEN 1 ELSE 0 END) AS delivered_orders_with_estimate
FROM analytics.fact_delivery
""").iloc[0].to_dict()
delivery_kpi["on_time_delivery_rate"] = (
    float(delivery_kpi["on_time_or_early_orders"])
    / float(delivery_kpi["delivered_orders_with_estimate"])
    if delivery_kpi["delivered_orders_with_estimate"]
    else None
)

exp = q("""
SELECT fr.valid_review_score AS review_score, fd.delivery_time_days, fd.delivery_gap_days, fd.order_freight_value, fd.freight_share
FROM analytics.fact_reviews fr
JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
WHERE fr.valid_review_score IS NOT NULL AND fd.is_delivered
""")
corr = (
    exp[
        [
            "review_score",
            "delivery_time_days",
            "delivery_gap_days",
            "order_freight_value",
            "freight_share",
        ]
    ]
    .corr(method="spearman")["review_score"]
    .to_dict()
)

by_bucket = q("""
SELECT fd.delivery_time_bucket, COUNT(*) AS reviews, AVG(fr.valid_review_score) AS avg_review_score
FROM analytics.fact_reviews fr
JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
WHERE fr.valid_review_score IS NOT NULL AND fd.delivery_time_bucket IS NOT NULL
GROUP BY fd.delivery_time_bucket
ORDER BY fd.delivery_time_bucket
""")
on_time = q("""
SELECT CASE WHEN fd.delivery_gap_days >= 0 THEN 'on_time_or_early' ELSE 'late' END AS timing,
       COUNT(*) AS reviews, AVG(fr.valid_review_score) AS avg_review_score
FROM analytics.fact_reviews fr
JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
WHERE fr.valid_review_score IS NOT NULL AND fd.delivery_gap_days IS NOT NULL AND fd.is_delivered
GROUP BY 1
""")
findings["experience_intelligence"] = {
    "grain": "review (fact_reviews) joined to order delivery (fact_delivery)",
    "filters": "valid_review_score IS NOT NULL; delivery KPIs over delivered orders with required dates",
    "kpis": {**review_kpi, **delivery_kpi},
    "spearman_corr_with_review": corr,
    "by_delivery_bucket": by_bucket.to_dict(orient="records"),
    "on_time_vs_late": on_time.to_dict(orient="records"),
}
by_bucket.to_csv(OUT_F / "delivery_bucket_reviews.csv", index=False)

plt.figure(figsize=(7, 4))
plt.bar(by_bucket["delivery_time_bucket"], by_bucket["avg_review_score"])
plt.title("Average Review Score by Delivery Time Bucket")
plt.ylabel("Avg review (1-5)")
plt.tight_layout()
plt.savefig(OUT_C / "review_by_delivery_bucket.png", dpi=150)
plt.close()

cat = q("""
WITH order_review AS (
  SELECT order_id, AVG(valid_review_score) AS avg_review_score
  FROM analytics.fact_reviews
  WHERE valid_review_score IS NOT NULL
  GROUP BY order_id
),
item_enriched AS (
  SELECT oi.order_id, oi.order_item_id,
         COALESCE(oi.product_category_name, 'unknown') AS category,
         oi.price, oi.freight_value
  FROM analytics.fact_order_items oi
)
SELECT category,
       COUNT(*) AS items,
       COUNT(DISTINCT i.order_id) AS orders,
       SUM(price) AS item_revenue,
       AVG(price) AS avg_item_price,
       AVG(r.avg_review_score) AS avg_review_score
FROM item_enriched i
LEFT JOIN order_review r ON i.order_id = r.order_id
GROUP BY category
ORDER BY item_revenue DESC
""")
cat.head(30).to_csv(OUT_F / "category_performance.csv", index=False)
findings["product_category"] = {
    "grain": "item (fact_order_items) with review averaged per order",
    "order_status_filter": "all",
    "top_categories_by_revenue": cat.head(15).to_dict(orient="records"),
}

geo = q("""
SELECT c.customer_state AS state,
       COUNT(DISTINCT o.order_id) AS order_count,
       COUNT(DISTINCT c.customer_unique_id) AS customers,
       SUM(o.order_total_value) AS gmv_payments,
       AVG(o.order_total_value) AS aov,
       AVG(CASE WHEN o.is_delivered AND o.delivery_time_days IS NOT NULL THEN o.delivery_time_days END) AS avg_delivery_days
FROM analytics.fact_orders o
JOIN analytics.dim_customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY gmv_payments DESC
""")
geo.to_csv(OUT_F / "state_performance.csv", index=False)
findings["geographic"] = {
    "grain": "order joined to customer (state)",
    "order_status_filter": "all orders for volume/value; avg_delivery_days over delivered orders with days",
    "by_state": geo.to_dict(orient="records"),
}

plt.figure(figsize=(10, 4))
top = geo.head(15)
plt.bar(top["state"], top["gmv_payments"])
plt.title("GMV (Payments) by Customer State (Top 15)")
plt.ylabel("BRL")
plt.tight_layout()
plt.savefig(OUT_C / "revenue_by_state.png", dpi=150)
plt.close()

findings["synthesis"] = {
    "overall": {
        "order_count": orders["order_count"],
        "gmv_payments": orders["gmv_payments"],
        "aov": orders["aov"],
        "median_order_value": orders["median_order_value"],
        "repeat_customer_rate": repeat["repeat_customer_rate"],
        "repeat_customers": repeat["repeat_customers"],
        "customers": repeat["customers"],
        "cancellation_rate": cancel["cancellation_rate"],
        "avg_review_score": review_kpi["avg_review_score"],
        "avg_delivery_days": delivery_kpi["avg_delivery_days"],
        "on_time_delivery_rate": delivery_kpi["on_time_delivery_rate"],
    }
}

Path(OUT_F / "analysis_findings.json").write_text(
    json.dumps(findings, indent=2, default=str), encoding="utf-8"
)
print("exported", len(findings), "domains")
