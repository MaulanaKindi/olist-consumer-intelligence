import json
import unittest
from pathlib import Path

DB = Path("db/olist.duckdb")
FINDINGS = Path("outputs/findings/analysis_findings.json")


class TestAnalyticsIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB.exists() or not FINDINGS.exists():
            raise unittest.SkipTest(
                "Requires db/olist.duckdb and outputs/findings/analysis_findings.json "
                "(run pipeline and export after placing data in data/raw/)"
            )
        import duckdb

        cls.conn = duckdb.connect(str(DB), read_only=True)

    @classmethod
    def tearDownClass(cls):
        conn = getattr(cls, "conn", None)
        if conn is not None:
            conn.close()

    def test_grain_fact_orders(self):
        total, distinct = self.conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT order_id) FROM analytics.fact_orders"
        ).fetchone()
        self.assertEqual(total, distinct)

    def test_repeat_customer_rate_matches_linkage(self):
        row = self.conn.execute("""
            WITH orders_per AS (
              SELECT cu.customer_unique_id, COUNT(DISTINCT o.order_id) cnt
              FROM staging.orders o
              JOIN staging.customers cu ON o.customer_id = cu.customer_id
              GROUP BY 1
            )
            SELECT COUNT(*), SUM(CASE WHEN cnt>1 THEN 1 ELSE 0 END) FROM orders_per
            """).fetchone()
        self.assertEqual(row, (96096, 2997))

    def test_dim_customers_repeat_consistent(self):
        row = self.conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN is_repeat_customer THEN 1 ELSE 0 END) FROM analytics.dim_customers"
        ).fetchone()
        self.assertEqual(row, (96096, 2997))

    def test_cancellation_rate_all_statuses(self):
        row = self.conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN order_status='canceled' THEN 1 ELSE 0 END) FROM analytics.fact_orders"
        ).fetchone()
        self.assertEqual(row, (99441, 625))

    def test_on_time_delivery_denominator(self):
        row = self.conn.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN delivery_gap_days >= 0 THEN 1 ELSE 0 END)
            FROM analytics.fact_delivery
            WHERE is_delivered AND delivery_gap_days IS NOT NULL
            """).fetchone()
        self.assertEqual(row, (96476, 89941))

    def test_findings_file_has_approved_kpis(self):
        data = json.loads(FINDINGS.read_text(encoding="utf-8"))
        self.assertEqual(data["kpi_governance"]["version"], "1.1")
        s = data["synthesis"]["overall"]
        for k in [
            "order_count",
            "gmv_payments",
            "aov",
            "repeat_customer_rate",
            "cancellation_rate",
            "on_time_delivery_rate",
            "avg_delivery_days",
            "avg_review_score",
        ]:
            self.assertIn(k, s)


if __name__ == "__main__":
    unittest.main()
