"""Focused tests for report synchronization contract (docs -> outputs/reports only)."""

from __future__ import annotations

from pathlib import Path

from scripts.export_analysis import sync_portfolio_reports
from tests.test_pipeline_integrity import _build_db_from_raw, make_synthetic_raw_dir


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_canonical_exec_overwrites_stale_mirror(tmp_path, capsys):
    docs_exec = tmp_path / "docs" / "executive_summary.md"
    docs_strat = tmp_path / "docs" / "strategic_recommendations.md"
    reports = tmp_path / "outputs" / "reports"
    mirror_exec = reports / "executive_intelligence_report.md"
    mirror_strat = reports / "strategic_opportunity_matrix.md"

    canonical_exec = (
        "# Executive\n\n**Project:** Olist Consumer & Marketplace Intelligence (OLIST-CI-02)\n"
    )
    canonical_strat = (
        "# Strategic\n\n**Project:** Olist Consumer & Marketplace Intelligence (OLIST-CI-02)\n"
    )
    _write(docs_exec, canonical_exec)
    _write(docs_strat, canonical_strat)
    _write(
        mirror_exec,
        "# Executive\n\n**Project:** Olist Consumer Intelligence & Market Intelligence Assessment (OLIST-CI-02)\n",
    )
    _write(mirror_strat, "old strategic")

    status = sync_portfolio_reports(docs_exec, docs_strat, reports)

    assert status == {"executive": True, "strategic": True}
    assert mirror_exec.read_text(encoding="utf-8") == canonical_exec
    assert mirror_strat.read_text(encoding="utf-8") == canonical_strat
    assert docs_exec.read_text(encoding="utf-8") == canonical_exec
    assert docs_strat.read_text(encoding="utf-8") == canonical_strat
    assert "WARNING" not in capsys.readouterr().out


def test_strategic_follows_same_direction(tmp_path):
    docs_exec = tmp_path / "docs" / "executive_summary.md"
    docs_strat = tmp_path / "docs" / "strategic_recommendations.md"
    reports = tmp_path / "outputs" / "reports"
    mirror_strat = reports / "strategic_opportunity_matrix.md"

    canonical_strat = "# Strategic\n\n**Project:** Olist Consumer & Marketplace Intelligence\nNEW\n"
    _write(docs_exec, "exec")
    _write(docs_strat, canonical_strat)
    _write(mirror_strat, "OLD_STALE_STRATEGIC")

    status = sync_portfolio_reports(docs_exec, docs_strat, reports)

    assert status["strategic"] is True
    assert mirror_strat.read_text(encoding="utf-8") == canonical_strat
    assert docs_strat.read_text(encoding="utf-8") == canonical_strat
    assert "OLD_STALE_STRATEGIC" not in docs_strat.read_text(encoding="utf-8")


def test_missing_canonical_source_warns_and_keeps_mirror(tmp_path, capsys):
    docs_exec = tmp_path / "docs" / "executive_summary.md"  # missing
    docs_strat = tmp_path / "docs" / "strategic_recommendations.md"
    reports = tmp_path / "outputs" / "reports"
    mirror_exec = reports / "executive_intelligence_report.md"
    mirror_strat = reports / "strategic_opportunity_matrix.md"

    stale_exec = "STALE_EXECUTIVE_MIRROR"
    canonical_strat = "CANONICAL_STRAT"
    _write(mirror_exec, stale_exec)
    _write(mirror_strat, "old")
    _write(docs_strat, canonical_strat)
    assert not docs_exec.exists()

    status = sync_portfolio_reports(docs_exec, docs_strat, reports)
    out = capsys.readouterr().out

    assert status["executive"] is False
    assert status["strategic"] is True
    assert not docs_exec.exists(), "missing canonical must not be created"
    assert mirror_exec.read_text(encoding="utf-8") == stale_exec
    assert "WARNING" in out
    assert "executive_summary.md" in out
    assert "incomplete" in out.lower()
    assert mirror_strat.read_text(encoding="utf-8") == canonical_strat


def test_custom_directories_respected(tmp_path):
    docs_exec = tmp_path / "custom_docs" / "exec.md"
    docs_strat = tmp_path / "custom_docs" / "strat.md"
    reports = tmp_path / "custom_out" / "reports_dir"
    _write(docs_exec, "EXEC_CANON")
    _write(docs_strat, "STRAT_CANON")

    status = sync_portfolio_reports(docs_exec, docs_strat, reports)

    assert status == {"executive": True, "strategic": True}
    assert (reports / "executive_intelligence_report.md").read_text(
        encoding="utf-8"
    ) == "EXEC_CANON"
    assert (reports / "strategic_opportunity_matrix.md").read_text(
        encoding="utf-8"
    ) == "STRAT_CANON"


def test_missing_canonical_export_completes_with_aggregate_warning(tmp_path, capsys):
    """Missing canonical -> item+aggregate warnings, mirror unchanged, export exits normally."""
    raw = make_synthetic_raw_dir(tmp_path)
    db = tmp_path / "syn.duckdb"
    conn = _build_db_from_raw(raw, db)
    conn.close()

    charts_dir = tmp_path / "charts"
    findings_dir = tmp_path / "findings"
    reports_dir = tmp_path / "reports"
    docs_assets = tmp_path / "docs_assets"
    docs_exec = tmp_path / "docs" / "executive_summary.md"  # missing canonical
    docs_strat = tmp_path / "docs" / "strategic_recommendations.md"
    for d in [charts_dir, findings_dir, reports_dir, docs_assets, docs_strat.parent]:
        d.mkdir(parents=True, exist_ok=True)

    _write(docs_strat, "CANONICAL_STRAT")
    _write(reports_dir / "executive_intelligence_report.md", "STALE_MIRROR_EXEC")
    assert not docs_exec.exists()

    import scripts.export_analysis as ea

    # no SystemExit / non-zero exit expected (normal completion)
    ea.main(
        [
            "--db-path",
            str(db),
            "--findings-dir",
            str(findings_dir),
            "--charts-dir",
            str(charts_dir),
            "--reports-dir",
            str(reports_dir),
            "--docs-assets-dir",
            str(docs_assets),
            "--docs-exec",
            str(docs_exec),
            "--docs-strat",
            str(docs_strat),
        ]
    )
    out = capsys.readouterr().out

    assert not docs_exec.exists(), "missing canonical must not be created"
    assert (reports_dir / "executive_intelligence_report.md").read_text(
        encoding="utf-8"
    ) == "STALE_MIRROR_EXEC"
    assert "executive" in out and "report synchronization incomplete" in out.lower()
    assert "WARNING: Portfolio report synchronization incomplete: executive" in out
    assert "Canonical docs remain authoritative" in out
    assert "existing mirrors were not used as fallback" in out
    assert "exported" in out  # analytical export completed normally
    assert (findings_dir / "analysis_findings.json").exists()


def test_skip_copy_docs_preserves_skip_behavior(tmp_path):
    """--skip-copy-docs skips chart curation and report mirroring."""
    raw = make_synthetic_raw_dir(tmp_path)
    db = tmp_path / "syn.duckdb"
    conn = _build_db_from_raw(raw, db)
    conn.close()

    charts_dir = tmp_path / "charts"
    findings_dir = tmp_path / "findings"
    reports_dir = tmp_path / "reports"
    docs_assets = tmp_path / "docs_assets"
    docs_exec = tmp_path / "docs" / "executive_summary.md"
    docs_strat = tmp_path / "docs" / "strategic_recommendations.md"
    for d in [charts_dir, findings_dir, reports_dir, docs_assets, docs_exec.parent]:
        d.mkdir(parents=True, exist_ok=True)

    canonical_exec = "CANONICAL_EXEC"
    canonical_strat = "CANONICAL_STRAT"
    _write(docs_exec, canonical_exec)
    _write(docs_strat, canonical_strat)
    _write(reports_dir / "executive_intelligence_report.md", "STALE_MIRROR_EXEC")
    _write(reports_dir / "strategic_opportunity_matrix.md", "STALE_MIRROR_STRAT")

    import scripts.export_analysis as ea

    ea.main(
        [
            "--db-path",
            str(db),
            "--findings-dir",
            str(findings_dir),
            "--charts-dir",
            str(charts_dir),
            "--reports-dir",
            str(reports_dir),
            "--docs-assets-dir",
            str(docs_assets),
            "--docs-exec",
            str(docs_exec),
            "--docs-strat",
            str(docs_strat),
            "--skip-copy-docs",
        ]
    )

    assert (reports_dir / "executive_intelligence_report.md").read_text(
        encoding="utf-8"
    ) == "STALE_MIRROR_EXEC"
    assert (reports_dir / "strategic_opportunity_matrix.md").read_text(
        encoding="utf-8"
    ) == "STALE_MIRROR_STRAT"
    assert docs_exec.read_text(encoding="utf-8") == canonical_exec
    assert docs_strat.read_text(encoding="utf-8") == canonical_strat
    assert not (docs_assets / "monthly_orders.png").exists()
    assert not (docs_assets / "review_by_delivery_bucket.png").exists()
    assert not (docs_assets / "revenue_by_state.png").exists()
    assert (findings_dir / "analysis_findings.json").exists()
