"""Tests for pipeline behavior and DB-backed integrity.

Synthetic/temporary tests run without the real Olist dataset or local DB artifacts.
Optional real-dataset acceptance checks are marked and only run when
OLIST_RUN_REAL_DATASET_TESTS=1 and required local artifacts exist.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import duckdb
import pytest

from src.config import DUCKDB_PATH, SOURCE_FILES
from src.db import get_connection
from src.grain_checks import run_grain_checks
from src.ingest import ingest_all
from src.pipeline import cmd_run, cmd_validate
from src.transform import transform_all

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("rows required")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def make_synthetic_raw_dir(base: Path) -> Path:
    """Create a minimal but referentially consistent synthetic Olist-like dataset."""
    raw = base / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    orders = [
        {
            "order_id": "o1",
            "customer_id": "c1",
            "order_status": "delivered",
            "order_purchase_timestamp": "2017-01-10 10:00:00",
            "order_approved_at": "2017-01-10 11:00:00",
            "order_delivered_carrier_date": "2017-01-12 10:00:00",
            "order_delivered_customer_date": "2017-01-15 10:00:00",
            "order_estimated_delivery_date": "2017-01-20 00:00:00",
        },
        {
            "order_id": "o2",
            "customer_id": "c2",
            "order_status": "canceled",
            "order_purchase_timestamp": "2017-02-05 09:00:00",
            "order_approved_at": "2017-02-05 10:00:00",
            "order_delivered_carrier_date": "",
            "order_delivered_customer_date": "",
            "order_estimated_delivery_date": "2017-02-20 00:00:00",
        },
        {
            "order_id": "o3",
            "customer_id": "c1b",
            "order_status": "delivered",
            "order_purchase_timestamp": "2017-03-01 08:00:00",
            "order_approved_at": "2017-03-01 09:00:00",
            "order_delivered_carrier_date": "2017-03-03 08:00:00",
            "order_delivered_customer_date": "2017-03-05 08:00:00",
            "order_estimated_delivery_date": "2017-03-04 00:00:00",
        },
    ]
    # customer_id c1 and c1b share same customer_unique_id -> repeat customer
    customers = [
        {
            "customer_id": "c1",
            "customer_unique_id": "u1",
            "customer_zip_code_prefix": "01001",
            "customer_city": "sao paulo",
            "customer_state": "SP",
        },
        {
            "customer_id": "c1b",
            "customer_unique_id": "u1",
            "customer_zip_code_prefix": "01002",
            "customer_city": "sao paulo",
            "customer_state": "SP",
        },
        {
            "customer_id": "c2",
            "customer_unique_id": "u2",
            "customer_zip_code_prefix": "20000",
            "customer_city": "rio de janeiro",
            "customer_state": "RJ",
        },
    ]
    order_items = [
        {
            "order_id": "o1",
            "order_item_id": "1",
            "product_id": "p1",
            "seller_id": "s1",
            "shipping_limit_date": "2017-01-11 00:00:00",
            "price": "100.00",
            "freight_value": "10.00",
        },
        {
            "order_id": "o1",
            "order_item_id": "2",
            "product_id": "p2",
            "seller_id": "s1",
            "shipping_limit_date": "2017-01-11 00:00:00",
            "price": "50.00",
            "freight_value": "5.00",
        },
        {
            "order_id": "o3",
            "order_item_id": "1",
            "product_id": "p1",
            "seller_id": "s2",
            "shipping_limit_date": "2017-03-02 00:00:00",
            "price": "80.00",
            "freight_value": "8.00",
        },
    ]
    payments = [
        {
            "order_id": "o1",
            "payment_sequential": "1",
            "payment_type": "credit_card",
            "payment_installments": "2",
            "payment_value": "165.00",
        },
        {
            "order_id": "o2",
            "payment_sequential": "1",
            "payment_type": "boleto",
            "payment_installments": "1",
            "payment_value": "0.00",
        },
        {
            "order_id": "o3",
            "payment_sequential": "1",
            "payment_type": "credit_card",
            "payment_installments": "1",
            "payment_value": "88.00",
        },
    ]
    # duplicate review_id linked to different orders with identical content (observed pattern)
    reviews = [
        {
            "review_id": "r_dup",
            "order_id": "o1",
            "review_score": "5",
            "review_comment_title": "ok",
            "review_comment_message": "great",
            "review_creation_date": "2017-01-16 00:00:00",
            "review_answer_timestamp": "2017-01-17 00:00:00",
        },
        {
            "review_id": "r_dup",
            "order_id": "o3",
            "review_score": "5",
            "review_comment_title": "ok",
            "review_comment_message": "great",
            "review_creation_date": "2017-01-16 00:00:00",
            "review_answer_timestamp": "2017-01-17 00:00:00",
        },
        {
            "review_id": "r2",
            "order_id": "o2",
            "review_score": "2",
            "review_comment_title": "",
            "review_comment_message": "late/cancel",
            "review_creation_date": "2017-02-25 00:00:00",
            "review_answer_timestamp": "2017-02-26 00:00:00",
        },
    ]
    products = [
        {
            "product_id": "p1",
            "product_category_name": "beleza_saude",
            "product_name_lenght": "10",
            "product_description_lenght": "100",
            "product_photos_qty": "1",
            "product_weight_g": "500",
            "product_length_cm": "10",
            "product_height_cm": "5",
            "product_width_cm": "8",
        },
        {
            "product_id": "p2",
            "product_category_name": "esporte_lazer",
            "product_name_lenght": "12",
            "product_description_lenght": "120",
            "product_photos_qty": "2",
            "product_weight_g": "300",
            "product_length_cm": "9",
            "product_height_cm": "4",
            "product_width_cm": "7",
        },
    ]
    sellers = [
        {
            "seller_id": "s1",
            "seller_zip_code_prefix": "01001",
            "seller_city": "sao paulo",
            "seller_state": "SP",
        },
        {
            "seller_id": "s2",
            "seller_zip_code_prefix": "20000",
            "seller_city": "rio de janeiro",
            "seller_state": "RJ",
        },
    ]
    geolocation = [
        {
            "geolocation_zip_code_prefix": "01001",
            "geolocation_lat": "-23.55",
            "geolocation_lng": "-46.63",
            "geolocation_city": "sao paulo",
            "geolocation_state": "SP",
        },
        {
            "geolocation_zip_code_prefix": "01001",
            "geolocation_lat": "-23.56",
            "geolocation_lng": "-46.62",
            "geolocation_city": "sao paulo",
            "geolocation_state": "SP",
        },
        {
            "geolocation_zip_code_prefix": "20000",
            "geolocation_lat": "-22.90",
            "geolocation_lng": "-43.17",
            "geolocation_city": "rio de janeiro",
            "geolocation_state": "RJ",
        },
    ]
    cat = [
        {
            "product_category_name": "beleza_saude",
            "product_category_name_english": "health_beauty",
        },
        {
            "product_category_name": "esporte_lazer",
            "product_category_name_english": "sports_leisure",
        },
    ]

    mapping = {
        "orders": orders,
        "order_items": order_items,
        "customers": customers,
        "products": products,
        "sellers": sellers,
        "payments": payments,
        "reviews": reviews,
        "geolocation": geolocation,
        "category_translation": cat,
    }
    for key, rows in mapping.items():
        _write_csv(raw / SOURCE_FILES[key], rows)
    return raw


def _build_db_from_raw(raw_dir: Path, db_path: Path) -> duckdb.DuckDBPyConnection:
    conn = get_connection(db_path=db_path)
    ingest_all(conn, data_dir=raw_dir, overwrite=True)
    transform_all(conn=conn)
    return conn


def _snapshot(db_path: Path) -> dict:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:

        def q(s: str):
            return conn.execute(s).fetchone()[0]

        grains = run_grain_checks(conn)
        return {
            "raw_orders": q("SELECT COUNT(*) FROM raw.orders"),
            "fact_orders": q("SELECT COUNT(*) FROM analytics.fact_orders"),
            "fact_reviews": q("SELECT COUNT(*) FROM analytics.fact_reviews"),
            "gmv": float(q("SELECT SUM(order_total_value) FROM analytics.fact_orders")),
            "grains_ok": all(g.get("valid") for g in grains),
        }
    finally:
        conn.close()


# ---------------------------- synthetic/clean-checkout tests ----------------------------


def test_pipeline_cmd_validate_respects_out_path(tmp_path, monkeypatch):
    raw = make_synthetic_raw_dir(tmp_path)
    db = tmp_path / "iso.duckdb"
    conn = _build_db_from_raw(raw, db)
    conn.close()

    default_dq = tmp_path / "default_findings" / "data_quality.json"
    # save_findings uses FINDINGS_DIR imported in src.validate
    monkeypatch.setattr("src.validate.FINDINGS_DIR", default_dq.parent, raising=False)
    monkeypatch.setattr("src.config.FINDINGS_DIR", default_dq.parent, raising=False)

    out = tmp_path / "artifacts" / "findings" / "data_quality.json"
    cmd_validate(db_path=db, out_path=out)
    assert out.exists()
    assert not default_dq.exists(), "non-default validate must not write default data_quality.json"


def test_cmd_run_non_default_db_isolates_outputs_and_preserves_defaults(tmp_path, monkeypatch):
    raw = make_synthetic_raw_dir(tmp_path)
    project = tmp_path / "project"
    (project / "docs" / "olist").mkdir(parents=True)
    (project / "outputs" / "findings").mkdir(parents=True)
    (project / "outputs" / "charts").mkdir(parents=True)
    (project / "outputs" / "reports").mkdir(parents=True)
    (project / "docs" / "assets").mkdir(parents=True)

    default_dq = project / "outputs" / "findings" / "data_quality.json"
    default_dq.write_text(json.dumps({"sentinel": True, "v": 1}), encoding="utf-8")
    default_exec = project / "docs" / "executive_summary.md"
    default_exec.write_text("DEFAULT_EXEC", encoding="utf-8")
    (project / "docs" / "olist" / "analytics_validation.json").write_text(
        '{"sentinel":1}', encoding="utf-8"
    )
    (project / "docs" / "olist" / "integrity_check.json").write_text(
        '{"sentinel":1}', encoding="utf-8"
    )

    # keep real PROJECT_ROOT so scripts are found; redirect config/output paths and raw inputs
    monkeypatch.setattr("src.config.RAW_DATA_DIR", raw)
    monkeypatch.setattr("src.config.FINDINGS_DIR", project / "outputs" / "findings")
    monkeypatch.setattr("src.config.CHARTS_DIR", project / "outputs" / "charts")
    monkeypatch.setattr("src.config.REPORTS_DIR", project / "outputs" / "reports")
    monkeypatch.setattr("src.validate.FINDINGS_DIR", project / "outputs" / "findings")
    monkeypatch.setattr("scripts.export_analysis.FINDINGS_DIR", project / "outputs" / "findings")
    monkeypatch.setattr("scripts.export_analysis.CHARTS_DIR", project / "outputs" / "charts")
    monkeypatch.setattr("scripts.export_analysis.REPORTS_DIR", project / "outputs" / "reports")
    monkeypatch.setattr("scripts.export_analysis.DOCS_ASSETS", project / "docs" / "assets")
    monkeypatch.setattr("scripts.export_analysis.DOCS_EXEC", default_exec)
    monkeypatch.setattr(
        "scripts.export_analysis.DOCS_STRAT", project / "docs" / "strategic_recommendations.md"
    )

    db = tmp_path / "empty_run.duckdb"
    cmd_run(overwrite=True, db_path=db)

    iso = db.parent / f".{db.stem}_artifacts"
    assert (iso / "findings" / "data_quality.json").exists()
    assert (iso / "analytics_validation.json").exists()
    assert (iso / "integrity_check.json").exists()
    assert (iso / "findings" / "analysis_findings.json").exists()

    # defaults must remain untouched
    assert json.loads(default_dq.read_text(encoding="utf-8")) == {"sentinel": True, "v": 1}
    assert default_exec.read_text(encoding="utf-8") == "DEFAULT_EXEC"
    assert json.loads(
        (project / "docs" / "olist" / "analytics_validation.json").read_text(encoding="utf-8")
    ) == {"sentinel": 1}
    assert json.loads(
        (project / "docs" / "olist" / "integrity_check.json").read_text(encoding="utf-8")
    ) == {"sentinel": 1}


def test_cold_start_and_repeat_run_isolated(tmp_path, monkeypatch):
    raw = make_synthetic_raw_dir(tmp_path)
    project = tmp_path / "project"
    for p in [
        project / "outputs" / "findings",
        project / "outputs" / "charts",
        project / "outputs" / "reports",
        project / "docs" / "olist",
        project / "docs" / "assets",
    ]:
        p.mkdir(parents=True)
    # keep real PROJECT_ROOT so scripts are found; redirect config/output paths and raw inputs
    monkeypatch.setattr("src.config.RAW_DATA_DIR", raw)
    monkeypatch.setattr("src.ingest.RAW_DATA_DIR", raw)
    monkeypatch.setattr("src.config.FINDINGS_DIR", project / "outputs" / "findings")
    monkeypatch.setattr("src.config.CHARTS_DIR", project / "outputs" / "charts")
    monkeypatch.setattr("src.config.REPORTS_DIR", project / "outputs" / "reports")
    monkeypatch.setattr("src.validate.FINDINGS_DIR", project / "outputs" / "findings")

    db = tmp_path / "cold.duckdb"
    assert not db.exists()
    cmd_run(overwrite=True, db_path=db)
    s1 = _snapshot(db)
    cmd_run(overwrite=True, db_path=db)
    s2 = _snapshot(db)

    for k in ["raw_orders", "fact_orders", "fact_reviews", "grains_ok"]:
        assert s1[k] == s2[k]
    assert abs(s1["gmv"] - s2["gmv"]) < 1e-6
    assert s1["raw_orders"] == 3 and s1["fact_reviews"] == 3 and s1["grains_ok"] is True

    # basic analytics/exports produced in isolated artifacts
    iso = db.parent / f".{db.stem}_artifacts"
    assert (iso / "analytics_validation.json").exists()
    assert (iso / "integrity_check.json").exists()
    # isolation: default project outputs not created
    assert not (project / "outputs" / "findings" / "data_quality.json").exists()


def test_fact_reviews_duplicate_review_id_preserved_as_review_order_pairs(tmp_path):
    raw = make_synthetic_raw_dir(tmp_path)
    db = tmp_path / "r.duckdb"
    conn = _build_db_from_raw(raw, db)
    try:
        row = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(DISTINCT (review_id,order_id)) FROM analytics.fact_reviews"
        ).fetchone()
        # 3 input rows: r_dup appears for 2 orders + r2
        assert row == (3, 2, 3)
        # duplicated review_id linked to different orders, identical content preserved
        dup = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT order_id), COUNT(DISTINCT review_score), COUNT(DISTINCT COALESCE(review_comment_message,'')) FROM analytics.fact_reviews WHERE review_id='r_dup'"
        ).fetchone()
        assert dup == (2, 2, 1, 1)
    finally:
        conn.close()


# ---------------------------- optional real-dataset acceptance (not clean-checkout default) ----------------------------


@pytest.mark.skipif(
    os.getenv("OLIST_RUN_REAL_DATASET_TESTS") != "1",
    reason="optional real-dataset acceptance tests (set OLIST_RUN_REAL_DATASET_TESTS=1)",
)
class TestRealDatasetAcceptance:
    @pytest.fixture(scope="class")
    def conn(self):
        if not DUCKDB_PATH.exists():
            pytest.skip(f"missing real DB: {DUCKDB_PATH}")
        c = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        yield c
        c.close()

    def test_real_grains(self, conn):
        for g in run_grain_checks(conn):
            assert g.get("valid"), g

    def test_real_fact_reviews_composite_grain(self, conn):
        row = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT (review_id, order_id)), COUNT(DISTINCT review_id) FROM analytics.fact_reviews"
        ).fetchone()
        assert row == (99224, 99224, 98410)

    def test_real_geographic_mapping(self, conn):
        row = conn.execute("""
            SELECT (SELECT COUNT(*) FROM analytics.fact_orders),
                   (SELECT COUNT(*) FROM analytics.fact_orders o JOIN staging.customers c ON o.customer_id=c.customer_id),
                   (SELECT COUNT(*) FROM staging.orders)
            """).fetchone()
        assert row == (99441, 99441, 99441)
