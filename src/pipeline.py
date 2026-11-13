"""Pipeline entry point for the Olist intelligence ETL and analysis."""

from __future__ import annotations

import sys

from .config import RAW_DATA_DIR
from .db import get_connection
from .grain_checks import run_grain_checks
from .ingest import ingest_all, list_source_files
from .transform import transform_all
from .validate import run_all_checks, save_findings


def cmd_ingest() -> None:
    """Ingest raw CSV files into DuckDB."""
    print("=== Ingestion Stage ===")
    source_status = list_source_files(RAW_DATA_DIR)
    missing = [k for k, v in source_status.items() if not v]
    if missing:
        print(f"Missing source files: {missing}")
        print(f"Please place CSV files in: {RAW_DATA_DIR}")
        sys.exit(1)

    conn = get_connection()
    try:
        results = ingest_all(conn)
        print(f"\nIngestion complete. Loaded {len(results)} tables.")
    finally:
        conn.close()


def cmd_validate() -> None:
    """Run data quality validation checks."""
    print("=== Validation Stage ===")
    conn = get_connection()
    try:
        results = run_all_checks(conn)
        output_path = save_findings(results)
        print(f"Validation complete. Results saved to: {output_path}")
    finally:
        conn.close()


def cmd_transform() -> None:
    """Run ETL transformation: raw -> staging -> analytics."""
    print("=== Transformation Stage ===")
    transform_all()
    print("Transformation complete.")


def cmd_grain_checks() -> None:
    """Run grain integrity checks on analytics tables."""
    print("=== Grain Check Stage ===")
    conn = get_connection()
    try:
        results = run_grain_checks(conn)
        all_valid = True
        for r in results:
            status = "PASS" if r.get("valid") else "FAIL"
            print(f"  {r['table']}: {status}")
            if not r.get("valid"):
                all_valid = False
                if "error" in r:
                    print(f"    Error: {r['error']}")
        if all_valid:
            print("\nAll grain checks passed.")
        else:
            print("\nSome grain checks failed. Review the output above.")
            sys.exit(1)
    finally:
        conn.close()


def cmd_run() -> None:
    """Run the full pipeline: ingest -> validate -> transform -> grain checks."""
    cmd_ingest()
    cmd_validate()
    cmd_transform()
    cmd_grain_checks()
    print("\n=== Pipeline Complete ===")


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline <command>")
        print("Commands: ingest, validate, transform, grain-checks, run")
        sys.exit(1)

    command = sys.argv[1].lower()
    commands = {
        "ingest": cmd_ingest,
        "validate": cmd_validate,
        "transform": cmd_transform,
        "grain-checks": cmd_grain_checks,
        "grain_checks": cmd_grain_checks,
        "run": cmd_run,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands)}")
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()
