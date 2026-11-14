"""Generate reproducible analysis findings and charts from DuckDB analytics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config import CHARTS_DIR, DUCKDB_PATH, FINDINGS_DIR, PROJECT_ROOT, REPORTS_DIR

DOCS_ASSETS = PROJECT_ROOT / "docs" / "assets"
DOCS_EXEC = PROJECT_ROOT / "docs" / "executive_summary.md"
DOCS_STRAT = PROJECT_ROOT / "docs" / "strategic_recommendations.md"

# Approved KPI filters (docs/olist/03_kpi_definitions.md v1.1):
# - Volume/value/repeat/cancellation: ALL order_status, purchase time basis.
# - avg_review_score: AVG(valid_review_score) over valid review-order records (grain review_id,order_id; pair-weighted), valid_review_score IS NOT NULL. Distinct review_id count reported separately where relevant.
# - on_time_delivery_rate: is_delivered AND delivery_gap_days IS NOT NULL.
# - avg_delivery_days: is_delivered AND delivery_time_days IS NOT NULL.
# Grain/filter/source stated per metric in outputs.


def q(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).fetchdf()


def ensure_dirs() -> None:
    for d in [FINDINGS_DIR, CHARTS_DIR, REPORTS_DIR, DOCS_ASSETS]:
        d.mkdir(parents=True, exist_ok=True)


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=str(DUCKDB_PATH))
    parser.add_argument("--findings-dir", type=str, default=str(FINDINGS_DIR))
    parser.add_argument("--charts-dir", type=str, default=str(CHARTS_DIR))
    parser.add_argument("--reports-dir", type=str, default=str(REPORTS_DIR))
    parser.add_argument("--docs-assets-dir", type=str, default=str(DOCS_ASSETS))
    parser.add_argument("--docs-exec", type=str, default=str(DOCS_EXEC))
    parser.add_argument("--docs-strat", type=str, default=str(DOCS_STRAT))
    parser.add_argument("--skip-copy-docs", action="store_true")
    args = parser.parse_args(argv)

    db_path = Path(args.db_path)
    findings_dir = Path(args.findings_dir)
    charts_dir = Path(args.charts_dir)
    reports_dir = Path(args.reports_dir)
    docs_assets = Path(args.docs_assets_dir)
    docs_exec = Path(args.docs_exec)
    docs_strat = Path(args.docs_strat)

    for d in [findings_dir, charts_dir, reports_dir] + (
        [] if args.skip_copy_docs else [docs_assets]
    ):
        d.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        findings: dict = {
            "kpi_governance": {
                "source": "docs/olist/03_kpi_definitions.md",
                "version": "1.1",
                "status_filter_default": "all order_status",
                "notes": "gmv_payments is payment-based order value (sum of payments). avg_review_score is mean over valid review-order records (fact_reviews grain review_id,order_id, pair-weighted; 99,224 valid records, 98,410 distinct review_id); distinct-review-id mean nearly identical in observed data. Review analyses preserve review-order associations.",
            }
        }

        dq_path = findings_dir / "data_quality.json"
        if dq_path.exists():
            dq = json.loads(dq_path.read_text(encoding="utf-8"))
            findings["data_quality"] = dq.get("results", dq)

        # 01 consumer behavior (approved KPIs)
        orders = (
            q(
                conn,
                """
            SELECT
              COUNT(DISTINCT order_id) AS order_count,
              SUM(order_total_value) AS gmv_payments,
              AVG(order_total_value) AS aov,
              quantile_cont(order_total_value, 0.5) AS median_order_value,
              AVG(order_items_count) AS avg_items_per_order
            FROM analytics.fact_orders
            """,
            )
            .iloc[0]
            .to_dict()
        )

        repeat = (
            q(
                conn,
                """
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
            """,
            )
            .iloc[0]
            .to_dict()
        )
        repeat["repeat_customer_rate"] = (
            float(repeat["repeat_customers"]) / float(repeat["customers"])
            if repeat["customers"]
            else None
        )

        cancel = (
            q(
                conn,
                """
            SELECT
              COUNT(*) AS orders_all,
              SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS canceled_orders
            FROM analytics.fact_orders
            """,
            )
            .iloc[0]
            .to_dict()
        )
        cancel["cancellation_rate"] = (
            float(cancel["canceled_orders"]) / float(cancel["orders_all"])
            if cancel["orders_all"]
            else None
        )

        status = q(
            conn,
            """
            SELECT order_status, COUNT(*) AS order_count
            FROM analytics.fact_orders
            GROUP BY order_status
            ORDER BY order_count DESC
            """,
        ).to_dict(orient="records")

        monthly = q(
            conn,
            """
            WITH bounds AS (
              SELECT date_trunc('month', MIN(order_purchase_timestamp)) AS min_m,
                     date_trunc('month', MAX(order_purchase_timestamp)) AS max_m
              FROM analytics.fact_orders
            ),
            months AS (
              SELECT generate_series AS month_start
              FROM generate_series(
                (SELECT min_m FROM bounds),
                (SELECT max_m FROM bounds),
                INTERVAL 1 MONTH
              )
            ),
            agg AS (
              SELECT date_trunc('month', order_purchase_timestamp) AS month_start,
                     COUNT(DISTINCT order_id) AS order_count,
                     SUM(order_total_value) AS gmv_payments
              FROM analytics.fact_orders
              GROUP BY 1
            )
            SELECT strftime(m.month_start, '%Y-%m') AS month,
                   COALESCE(a.order_count, 0) AS order_count,
                   COALESCE(a.gmv_payments, 0.0) AS gmv_payments,
                   CASE WHEN strftime(m.month_start, '%Y-%m') IN ('2016-09','2018-09','2018-10') THEN true ELSE false END AS is_partial_boundary_month
            FROM months m
            LEFT JOIN agg a ON m.month_start = a.month_start
            ORDER BY m.month_start
            """,
        )
        monthly.to_csv(findings_dir / "monthly_orders.csv", index=False)

        findings["consumer_behavior"] = {
            "grain": "order (fact_orders), customer_unique_id (staging.customers+orders for repeat)",
            "order_status_filter": "all",
            "kpis": {**orders, **repeat, **cancel},
            "order_status_distribution": status,
        }

        plt.figure(figsize=(11, 4))
        x = monthly["month"]
        y = monthly["order_count"]
        plt.plot(x, y, marker="o", color="#4C72B0", label="Observed orders")
        # highlight boundary months
        boundary = monthly[monthly["is_partial_boundary_month"]]
        if not boundary.empty:
            plt.scatter(
                boundary["month"],
                boundary["order_count"],
                color="#C44E52",
                zorder=3,
                label="Partial boundary month",
            )
        plt.xticks(rotation=45, ha="right")
        plt.title("Monthly Order Count (all statuses, complete month spine)")
        plt.ylabel("Orders")
        plt.annotate(
            "Observed period: 2016-09-04 to 2018-10-17; 2016-09 and 2018-09/2018-10 are partial",
            xy=(0.01, -0.28),
            xycoords="axes fraction",
            fontsize=8,
            color="#444444",
        )
        plt.legend(loc="upper left", fontsize=8)
        plt.tight_layout()
        plt.savefig(charts_dir / "monthly_orders.png", dpi=150, bbox_inches="tight")
        plt.close()

        # 02 experience intelligence
        review_kpi = (
            q(
                conn,
                """
            SELECT AVG(valid_review_score) AS avg_review_score,
                   COUNT(*) AS reviews_valid
            FROM analytics.fact_reviews
            WHERE valid_review_score IS NOT NULL
            """,
            )
            .iloc[0]
            .to_dict()
        )

        delivery_kpi = (
            q(
                conn,
                """
            SELECT
              AVG(CASE WHEN is_delivered AND delivery_time_days IS NOT NULL THEN delivery_time_days END) AS avg_delivery_days,
              SUM(CASE WHEN is_delivered AND delivery_time_days IS NOT NULL THEN 1 ELSE 0 END) AS delivered_orders_with_days,
              SUM(CASE WHEN is_delivered AND delivery_gap_days IS NOT NULL AND delivery_gap_days >= 0 THEN 1 ELSE 0 END) AS on_time_or_early_orders,
              SUM(CASE WHEN is_delivered AND delivery_gap_days IS NOT NULL THEN 1 ELSE 0 END) AS delivered_orders_with_estimate
            FROM analytics.fact_delivery
            """,
            )
            .iloc[0]
            .to_dict()
        )
        delivery_kpi["on_time_delivery_rate"] = (
            float(delivery_kpi["on_time_or_early_orders"])
            / float(delivery_kpi["delivered_orders_with_estimate"])
            if delivery_kpi["delivered_orders_with_estimate"]
            else None
        )

        exp = q(
            conn,
            """
            SELECT fr.valid_review_score AS review_score,
                   fd.delivery_time_days,
                   fd.delivery_gap_days,
                   fd.order_freight_value,
                   fd.freight_share
            FROM analytics.fact_reviews fr
            JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
            WHERE fr.valid_review_score IS NOT NULL AND fd.is_delivered
            """,
        )
        cols = [
            "review_score",
            "delivery_time_days",
            "delivery_gap_days",
            "order_freight_value",
            "freight_share",
        ]
        pearson = exp[cols].corr(method="pearson")["review_score"].to_dict()
        spearman = exp[cols].corr(method="spearman")["review_score"].to_dict()

        bucket_order = ["0-3 days", "4-7 days", "8-14 days", "15-30 days", "30+ days"]
        by_bucket = q(
            conn,
            """
            SELECT fd.delivery_time_bucket,
                   COUNT(*) AS reviews,
                   AVG(fr.valid_review_score) AS avg_review_score
            FROM analytics.fact_reviews fr
            JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
            WHERE fr.valid_review_score IS NOT NULL AND fd.delivery_time_bucket IS NOT NULL
            GROUP BY fd.delivery_time_bucket
            """,
        )
        by_bucket["delivery_time_bucket"] = pd.Categorical(
            by_bucket["delivery_time_bucket"], categories=bucket_order, ordered=True
        )
        by_bucket = by_bucket.sort_values("delivery_time_bucket")
        by_bucket.to_csv(findings_dir / "delivery_bucket_reviews.csv", index=False)

        on_time = q(
            conn,
            """
            SELECT CASE WHEN fd.delivery_gap_days >= 0 THEN 'on_time_or_early' ELSE 'late' END AS timing,
                   COUNT(*) AS reviews,
                   AVG(fr.valid_review_score) AS avg_review_score
            FROM analytics.fact_reviews fr
            JOIN analytics.fact_delivery fd ON fr.order_id = fd.order_id
            WHERE fr.valid_review_score IS NOT NULL
              AND fd.delivery_gap_days IS NOT NULL
              AND fd.is_delivered
            GROUP BY 1
            """,
        )

        findings["experience_intelligence"] = {
            "grain": "review-order (fact_reviews review_id,order_id) joined to order delivery (fact_delivery)",
            "filters": "valid_review_score IS NOT NULL; delivery KPIs over delivered orders with required dates",
            "kpis": {**review_kpi, **delivery_kpi},
            "correlations": {
                "method_note": "Pearson via pandas .corr(method='pearson'); Spearman via pandas .corr(method='spearman') on the same filtered sample.",
                "pearson_with_review": pearson,
                "spearman_with_review": spearman,
            },
            "by_delivery_bucket": by_bucket.to_dict(orient="records"),
            "on_time_vs_late": on_time.to_dict(orient="records"),
        }

        plt.figure(figsize=(8, 4.5))
        bars = plt.bar(
            by_bucket["delivery_time_bucket"].astype(str),
            by_bucket["avg_review_score"],
            color="#4C72B0",
        )
        plt.title("Average Review Score by Delivery Time Bucket")
        plt.ylabel("Avg review (1-5)")
        plt.xlabel("Delivery time bucket (chronological)")
        for bar, n in zip(bars, by_bucket["reviews"]):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"n={int(n):,}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        plt.ylim(0, 5.2)
        plt.tight_layout()
        plt.savefig(charts_dir / "review_by_delivery_bucket.png", dpi=150)
        plt.close()

        # 03 product/category (order-category grain for reviews)
        cat = q(
            conn,
            """
            WITH valid_review AS (
              SELECT review_id, order_id, valid_review_score
              FROM analytics.fact_reviews
              WHERE valid_review_score IS NOT NULL
            ),
            order_category AS (
              SELECT DISTINCT
                oi.order_id,
                COALESCE(oi.product_category_name, 'unknown') AS category
              FROM analytics.fact_order_items oi
            ),
            item_metrics AS (
              SELECT
                COALESCE(oi.product_category_name, 'unknown') AS category,
                COUNT(*) AS items,
                COUNT(DISTINCT oi.order_id) AS orders,
                SUM(oi.price) AS item_revenue,
                AVG(oi.price) AS avg_item_price
              FROM analytics.fact_order_items oi
              GROUP BY 1
            ),
            review_metrics AS (
              SELECT
                oc.category,
                COUNT(DISTINCT vr.order_id) AS orders_with_review,
                COUNT(*) AS review_order_pairs,
                AVG(vr.valid_review_score) AS avg_review_score
              FROM order_category oc
              JOIN valid_review vr ON oc.order_id = vr.order_id
              GROUP BY oc.category
            )
            SELECT
              i.category,
              i.items,
              i.orders,
              i.item_revenue,
              i.avg_item_price,
              COALESCE(r.orders_with_review, 0) AS orders_with_review,
              COALESCE(r.review_order_pairs, 0) AS review_order_pairs,
              r.avg_review_score
            FROM item_metrics i
            LEFT JOIN review_metrics r ON i.category = r.category
            ORDER BY i.item_revenue DESC
            """,
        )
        cat.head(30).to_csv(findings_dir / "category_performance.csv", index=False)
        findings["product_category"] = {
            "grain": "items/orders at item-order grain; review metrics at distinct (order_id, category) grain",
            "order_status_filter": "all",
            "review_definition": "Average order-level review among orders containing the category (order-category pairs; same order may contribute to multiple categories).",
            "top_categories_by_revenue": cat.head(15).to_dict(orient="records"),
        }

        # 04 geographic (order-level state via staging.customers.customer_id)
        geo = q(
            conn,
            """
            SELECT cu.customer_state AS state,
                   COUNT(DISTINCT o.order_id) AS order_count,
                   COUNT(DISTINCT cu.customer_unique_id) AS customers,
                   SUM(o.order_total_value) AS gmv_payments,
                   AVG(o.order_total_value) AS aov,
                   AVG(CASE WHEN o.is_delivered AND o.delivery_time_days IS NOT NULL THEN o.delivery_time_days END) AS avg_delivery_days
            FROM analytics.fact_orders o
            JOIN staging.customers cu ON o.customer_id = cu.customer_id
            GROUP BY cu.customer_state
            ORDER BY gmv_payments DESC
            """,
        )
        geo.to_csv(findings_dir / "state_performance.csv", index=False)
        findings["geographic"] = {
            "grain": "order (fact_orders) joined to order-level customer location via staging.customers.customer_id",
            "order_status_filter": "all orders for volume/value; avg_delivery_days over delivered orders with days",
            "reconciliation": {
                "total_orders": int(geo["order_count"].sum()) if not geo.empty else 0,
                "total_gmv_payments": float(geo["gmv_payments"].sum()) if not geo.empty else 0.0,
            },
            "by_state": geo.to_dict(orient="records"),
        }

        plt.figure(figsize=(10, 4))
        top = geo.head(15)
        plt.bar(top["state"], top["gmv_payments"], color="#4C72B0")
        plt.title("GMV (Payments) by Customer State (Top 15)")
        plt.ylabel("BRL")
        plt.xlabel("Customer state (order-level location)")
        plt.tight_layout()
        plt.savefig(charts_dir / "revenue_by_state.png", dpi=150)
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

        (findings_dir / "analysis_findings.json").write_text(
            json.dumps(findings, indent=2, default=str), encoding="utf-8"
        )

        # Copy curated portfolio artifacts (skip when testing isolated DB)
        if not args.skip_copy_docs:
            for name in [
                "monthly_orders.png",
                "review_by_delivery_bucket.png",
                "revenue_by_state.png",
            ]:
                copy_if_exists(charts_dir / name, docs_assets / name)
            copy_if_exists(reports_dir / "executive_intelligence_report.md", docs_exec)
            copy_if_exists(reports_dir / "strategic_opportunity_matrix.md", docs_strat)

        print("exported", len(findings), "domains")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
