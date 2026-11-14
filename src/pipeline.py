"""Pipeline entry point for the Olist intelligence ETL and analysis."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

from .config import PROJECT_ROOT
from .db import get_connection
from .grain_checks import run_grain_checks
from .ingest import ingest_all
from .transform import transform_all
from .validate import run_all_checks, save_findings


def _run_script(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required script not found: {path}")
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as e:
        if e.code not in (0, None):
            raise


def _fail(msg: str) -> None:
    print(msg)
    raise SystemExit(1)


def cmd_ingest(overwrite: bool = False, db_path: Path | None = None) -> None:
    """Ingest raw CSV files into DuckDB."""
    print("=== Ingestion Stage ===")
    conn = get_connection(db_path=db_path)
    try:
        results = ingest_all(conn, overwrite=overwrite)
        print(f"Ingestion complete. Loaded {len(results)} tables.")
    finally:
        conn.close()


def cmd_validate(db_path: Path | None = None, out_path: Path | None = None) -> None:
    """Run data quality validation checks."""
    print("=== Validation Stage ===")
    conn = get_connection(db_path=db_path)
    try:
        results = run_all_checks(conn)
        output_path = save_findings(results, output_path=out_path)
        print(f"Validation complete. Results saved to: {output_path}")
    finally:
        conn.close()


def cmd_transform(db_path: Path | None = None) -> None:
    """Run ETL transformation: raw -> staging -> analytics."""
    print("=== Transformation Stage ===")
    conn = get_connection(db_path=db_path)
    try:
        transform_all(conn=conn)
    finally:
        conn.close()
    print("Transformation complete.")


def cmd_grain_checks(db_path: Path | None = None) -> list[dict]:
    """Run grain integrity checks on analytics tables."""
    print("=== Grain Check Stage ===")
    conn = get_connection(db_path=db_path)
    try:
        results = run_grain_checks(conn)
        all_valid = True
        for r in results:
            status = "PASS" if r.get("valid") else "FAIL"
            extra = f" ({r.get('error')})" if r.get("error") else ""
            print(f"  {r['table']}: {status}{extra}")
            if not r.get("valid"):
                all_valid = False
        if not all_valid:
            _fail("Grain checks failed.")
        print("All grain checks passed.")
        return results
    finally:
        conn.close()


def cmd_analytics_validation(db_path: Path | None = None, out_path: Path | None = None) -> None:
    """Run analytics transformation reconciliation checks."""
    print("=== Analytics Validation Stage ===")
    script = PROJECT_ROOT / "scripts" / "validate_analytics.py"
    args: list[str] = []
    if db_path is not None:
        args += ["--db-path", str(db_path)]
    if out_path is not None:
        args += ["--out", str(out_path)]
    # run script in-process with argv
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(script)] + args
        _run_script(script)
    finally:
        sys.argv = old_argv
    out = out_path or (PROJECT_ROOT / "docs" / "olist" / "analytics_validation.json")
    data = json.loads(out.read_text(encoding="utf-8"))
    grain_ok = all(r.get("valid") for r in data.get("grain", []))
    transform_ok = all(r.get("valid") for r in data.get("transforms", []))
    if not (grain_ok and transform_ok):
        _fail("Analytics validation failed.")
    print("Analytics validation passed.")


def cmd_integrity(db_path: Path | None = None, out_path: Path | None = None) -> None:
    """Run referential integrity checks."""
    print("=== Integrity Check Stage ===")
    script = PROJECT_ROOT / "scripts" / "check_integrity.py"
    args: list[str] = []
    if db_path is not None:
        args += ["--db-path", str(db_path)]
    if out_path is not None:
        args += ["--out", str(out_path)]
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(script)] + args
        _run_script(script)
    finally:
        sys.argv = old_argv
    out = out_path or (PROJECT_ROOT / "docs" / "olist" / "integrity_check.json")
    data = json.loads(out.read_text(encoding="utf-8"))
    failed = [k for k, v in data.items() if isinstance(v, dict) and v.get("status") == "FAIL"]
    if failed:
        _fail(f"Integrity checks failed: {failed}")
    print("Integrity checks passed.")


def cmd_export(
    db_path: Path | None = None,
    findings_dir: Path | None = None,
    charts_dir: Path | None = None,
    reports_dir: Path | None = None,
    skip_copy_docs: bool = False,
) -> None:
    """Generate analytical findings and charts."""
    print("=== Export Stage ===")
    script = PROJECT_ROOT / "scripts" / "export_analysis.py"
    args: list[str] = []
    if db_path is not None:
        args += ["--db-path", str(db_path)]
    if findings_dir is not None:
        args += ["--findings-dir", str(findings_dir)]
    if charts_dir is not None:
        args += ["--charts-dir", str(charts_dir)]
    if reports_dir is not None:
        args += ["--reports-dir", str(reports_dir)]
    if skip_copy_docs:
        args += ["--skip-copy-docs"]
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(script)] + args
        _run_script(script)
    finally:
        sys.argv = old_argv
    print("Export complete.")


def cmd_run(overwrite: bool = False, db_path: Path | None = None) -> None:
    """Run the full pipeline end-to-end."""
    cmd_ingest(overwrite=overwrite, db_path=db_path)
    # When targeting a non-default DB, keep all validation/export artifacts isolated.
    if db_path is not None:
        tmp = db_path.parent / f".{db_path.stem}_artifacts"
        tmp.mkdir(parents=True, exist_ok=True)
        cmd_validate(db_path=db_path, out_path=tmp / "findings" / "data_quality.json")
        cmd_transform(db_path=db_path)
        cmd_grain_checks(db_path=db_path)
        cmd_analytics_validation(db_path=db_path, out_path=tmp / "analytics_validation.json")
        cmd_integrity(db_path=db_path, out_path=tmp / "integrity_check.json")
        cmd_export(
            db_path=db_path,
            findings_dir=tmp / "findings",
            charts_dir=tmp / "charts",
            reports_dir=tmp / "reports",
            skip_copy_docs=True,
        )
    else:
        cmd_validate(db_path=db_path)
        cmd_transform(db_path=db_path)
        cmd_grain_checks(db_path=db_path)
        cmd_analytics_validation(db_path=db_path)
        cmd_integrity(db_path=db_path)
        cmd_export()
    print("\n=== Pipeline Complete ===")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="python -m src.pipeline")
    parser.add_argument(
        "command",
        choices=[
            "ingest",
            "validate",
            "transform",
            "grain-checks",
            "grain_checks",
            "analytics-validate",
            "integrity",
            "export",
            "run",
        ],
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="For ingest/run: replace existing raw tables (explicit full rebuild).",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Optional DuckDB path (default: project db/olist.duckdb).",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.db_path) if args.db_path else None
    cmd = args.command

    if cmd == "ingest":
        cmd_ingest(overwrite=args.overwrite, db_path=db_path)
    elif cmd == "validate":
        cmd_validate(db_path=db_path)
    elif cmd == "transform":
        cmd_transform(db_path=db_path)
    elif cmd in {"grain-checks", "grain_checks"}:
        cmd_grain_checks(db_path=db_path)
    elif cmd == "analytics-validate":
        cmd_analytics_validation(db_path=db_path)
    elif cmd == "integrity":
        cmd_integrity(db_path=db_path)
    elif cmd == "export":
        cmd_export()
    elif cmd == "run":
        cmd_run(overwrite=args.overwrite, db_path=db_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
