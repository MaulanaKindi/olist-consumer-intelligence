# Olist Consumer Intelligence & Market Intelligence Assessment

An evidence-based consumer and marketplace intelligence study using historical transaction, delivery, review, product, and geographic data from the **Brazilian E-Commerce Public Dataset by Olist** (Kaggle, observed period **2016–2018**).

**Source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
**Attribution:** Dataset provided by Olist on Kaggle; subject to the source license/terms. See `docs/dataset_license_notes.md` before public release or redistribution.

---

## Project Structure

```text
olist-consumer-intelligence/
├── data/raw/                    # Source CSVs (gitignored)
├── db/                          # DuckDB warehouse (gitignored)
├── docs/                        # Charter, research design, architecture, data dictionary, Olist refs, license notes
├── notebooks/                   # 00–05 analysis notebooks (grain-aligned, executed)
├── outputs/                     # Regenerable findings/charts/reports (gitignored by default)
├── queries/                     # SQL: 01_staging.sql, 02_analytics.sql
├── scripts/                     # Build/validate/profile/export utilities
├── src/                         # Pipeline modules (ingest, validate, transform, grain checks)
├── tests/                       # Integrity/KPI tests
└── README.md
```

## Status & Progress

- **Milestone 1 (M1): Project Scoping & Charter** — Completed & Approved
- **Milestone 2 (M2): Research Design & Framework** — Completed (research design, approved KPI dictionary, data dictionary, architecture)
- **Milestone 3 (M3): Data Pipeline & Quality** — Completed (raw→staging→analytics in DuckDB, validation, grain checks)
- **Milestone 4 (M4): Domain Analysis & Synthesis** — Completed (notebooks 00–05 aligned to analytics grain, exported findings/charts)
- **Milestone 5 (M5): Reporting** — Completed (executive intelligence report, strategic opportunity matrix)

## Reproducibility

1. Place Kaggle Olist CSVs in `data/raw/` (see `src/config.py`).
2. Run pipeline: `python -m src.pipeline run` (or stages: `ingest`, `validate`, `transform`, `grain-checks`). If raw tables already exist, run `validate`/`transform`/`grain-checks` as needed.
3. Export analysis artifacts: `python scripts/export_analysis.py`.
4. Execute notebooks 00–05 top-to-bottom (requires `PYTHONPATH` including project root) and/or run tests: `python -m pytest -q`.
5. Key outputs (regenerable): `outputs/findings/*`, `outputs/charts/*.png`, `outputs/reports/*.md`, `docs/olist/analytics_validation.json`.

## Notes and Limitations

- **Observational scope:** 2016–2018 Olist marketplace sample; findings describe associations, not causation, and do not represent the full Brazilian e-commerce market.
- **KPI governance:** Metrics follow approved definitions/filters in `docs/olist/03_kpi_definitions.md` (single source of truth). Every reported metric states source table, `order_status` filter, and grain.
- **Data handling:** Original category values preserved as-is; translations documented separately. Raw data/DB are gitignored; verify dataset license/terms and attribution before publication (`docs/dataset_license_notes.md`).