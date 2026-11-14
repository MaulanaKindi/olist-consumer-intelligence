"""Synthetic unit tests (no real Olist dataset required)."""

from __future__ import annotations

import duckdb
import pandas as pd

from src.grain_checks import check_grain
from src.validate import check_referential_integrity, check_review_score_range


def _conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    c.execute("CREATE SCHEMA raw; CREATE SCHEMA staging; CREATE SCHEMA analytics;")
    return c


def test_grain_empty_table_invalid():
    c = _conn()
    c.execute("CREATE TABLE analytics.t (id INTEGER)")
    r = check_grain(c, "t", ["id"], allow_empty=False)
    assert r["valid"] is False and r["error"] == "empty_table"


def test_grain_duplicates_nulls_and_valid():
    c = _conn()
    c.execute("CREATE TABLE analytics.t (id INTEGER)")
    c.execute("INSERT INTO analytics.t VALUES (1),(1),(NULL)")
    r = check_grain(c, "t", ["id"], allow_empty=False)
    # duplicate_key_rows counts rows in duplicated key groups (2 rows share id=1)
    assert r["valid"] is False and r["duplicate_key_rows"] == 2 and r["null_key_rows"] == 1

    c.execute("DELETE FROM analytics.t")
    c.execute("INSERT INTO analytics.t VALUES (1),(2)")
    r = check_grain(c, "t", ["id"], allow_empty=False)
    assert r["valid"] is True and r["duplicate_key_rows"] == 0 and r["null_key_rows"] == 0


def test_grain_allow_empty():
    c = _conn()
    c.execute("CREATE TABLE analytics.t (id INTEGER)")
    r = check_grain(c, "t", ["id"], allow_empty=True)
    assert r["valid"] is True and r["error"] is None


def test_review_score_validation_counts():
    c = _conn()
    c.execute("CREATE TABLE raw.reviews (review_score VARCHAR)")
    c.execute("INSERT INTO raw.reviews VALUES ('5'), ('1'), ('0'), ('6'), ('abc'), (NULL)")
    r = check_review_score_range(c)
    assert r["total"] == 6
    assert r["valid"] == 2
    assert r["null"] == 1
    assert r["non_numeric"] == 1
    assert r["out_of_range"] == 2
    assert r["invalid"] == 4


def test_referential_integrity_not_exists_handles_nulls():
    c = _conn()
    c.execute("CREATE TABLE raw.parent (id INTEGER)")
    c.execute("CREATE TABLE raw.child (pid INTEGER)")
    c.execute("INSERT INTO raw.parent VALUES (1),(NULL)")
    c.execute("INSERT INTO raw.child VALUES (1),(2),(NULL)")
    r = check_referential_integrity(c, "child", "pid", "parent", "id")
    assert r["total"] == 3
    assert r["null_fk"] == 1
    assert r["orphaned"] == 1  # pid=2 only
    assert r["integrity_rate"] == 0.5


def test_correlation_methods_distinct():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 10], "y": [1, 4, 9, 16, 25]})
    pearson = df.corr(method="pearson").loc["x", "y"]
    spearman = df.corr(method="spearman").loc["x", "y"]
    assert abs(pearson - spearman) > 1e-9
    assert spearman == 1.0
