# Remediation Reconciliation (Before / After)

**Project:** OLIST-CI-02 — Olist Consumer Intelligence
**Branch:** `fix/olist-analytical-integrity`
**Date:** 2026-11-14
**Evidence sources:** `docs/olist/analytics_validation.json`, `docs/olist/integrity_check.json`, `outputs/findings/analysis_findings.json`, `outputs/findings/data_quality.json`, executed notebooks `00-05`, pipeline/test runs recorded below. Baseline artifacts preserved in `backup/pre-remediation/`.

## 1. Summary

| Area | Previous state (reported/baseline risk) | Corrected state (current) | Validation evidence | Impact |
|---|---|---|---|---|
| Geographic order mapping | Order-level geography at risk of incomplete/misaligned mapping when using representative `customer_unique_id` dimension joins | Order-level geo joins `analytics.fact_orders` to `staging.customers` on `customer_id`; `dim_customers` remains 1 row per `customer_unique_id` with representative `customer_id` and aggregates | `analytics_validation`: geographic mapping 99,441/99,441/99,441 VALID; `analysis_findings.geographic.reconciliation` total_orders 99,441, gmv ~16,008,872.12; notebook 04 reconciliation | Eliminates order-coverage distortion in geographic KPIs; SP/top-state figures reconciled to full order population |
| Review fact grain & duplicates | Raw `reviews.review_id` not unique; risk of over-dedup or wrong grain | `analytics.fact_reviews` grain `(review_id, order_id)`; deterministic dedup of exact review-order rows; preserves duplicate review IDs linked to different orders (789 IDs) | DQ: `primary_key_uniqueness.reviews=false`; grain/analytics validation: fact_reviews 99,224 rows, 99,224 distinct keys, VALID; integrity tests pass | Prevents loss/inflation of review-order evidence and makes review joins auditable |
| Category review interpretation | Risk of item-weighted or causally phrased category satisfaction | Avg order-level review among orders containing category at distinct `(order_id, category)`; documented as non-causal | `scripts/export_analysis.py`, notebook 03, reports/docs updated | Correct interpretation: segment experience signal, not item-level product quality proof |
| Item counts (products/sellers) | Risk of incorrect item aggregation grain | `total_items_sold = COUNT(order_item_id)` at item grain; reconciled to `staging.order_items` | `analytics_validation` mismatches 0 for dim_products/dim_sellers; `tests/test_pipeline_integrity.py` | Accurate volume metrics per product/seller |
| Correlation methods | Risk of labeling `corr()` as Spearman | Pearson and Spearman computed explicitly via pandas (`corr(method='pearson'|'spearman')`) and reported separately | `analysis_findings.experience_intelligence.correlations`, notebook 02, synthetic test `test_correlation_methods_distinct` | Methodologically correct association reporting (Pearson ~-0.334, Spearman ~-0.235 for delivery days vs review on filtered sample) |
| Monthly trends | Risk of implying comparable endpoints/missing months | Complete month spine; partial boundary months 2016-09/2018-09/2018-10 flagged; 2016-11 present as zero in spine logic as applicable | `outputs/findings/monthly_orders.csv`, export/chart logic, notebook 01 | Prevents misleading trend interpretation at period edges |
| Delivery buckets & ordering | Risk of lexical/incorrect ordering | Chronological bucket ordering enforced (0-3,4-7,8-14,15-30,30+) | `delivery_bucket_reviews.csv`, chart/export/notebook 02 | Correct gradient interpretation |
| KPI definitions | Risk of ambiguous GMV/status semantics | `docs/olist/03_kpi_definitions.md` v1.1 APPROVED; `gmv_payments` = payment-based order value (sum of payments), all-status default with explicit delivery/review constraints | Docs/exports/reports aligned; findings `kpi_governance.version=1.1` | Consistent, auditable KPI reporting |
| Pipeline repeatability & isolation | `pipeline run` ingest failed on existing raw tables; DB locks observed; non-default db-path side effects possible | `--overwrite` explicit; scripts accept `--db-path`/outputs options; `pipeline run --db-path` isolates validation/export artifacts under `db/.<stem>_artifacts/` and skips docs-copy | Two sequential `run --overwrite --db-path db/olist_test_pipeline.duckdb` runs PASS with consistent metrics (see below); sequential execution documented | Safer rebuilds/tests; no accidental overwrite of main docs/outputs when targeting isolated DB (after fix) |
| Quality gates & tests | Baseline gaps in synthetic/unit coverage and pipeline isolation | Lint/format/type/tests/gates passing in current state; synthetic/temporary tests added; optional real-dataset acceptance tests gated by `OLIST_RUN_REAL_DATASET_TESTS=1` | `ruff check .` PASS, `black --check .` PASS, `mypy src --ignore-missing-imports` PASS, `pytest -q` 10 passed / 3 skipped (local), grain/analytics/integrity PASS | Higher confidence in validation logic and reproducible CI/local checks |

## 2. Numerical Reconciliation (current, verified)

| Metric | Value (current) | Source/grain/filter | Evidence |
|---|---:|---|---|
| `order_count` | 99,441 | `analytics.fact_orders`, all statuses | findings/validation/tests |
| `gmv_payments` (payment-based) | 16,008,872.12 BRL (approx) | sum of `fact_orders.order_total_value`, all statuses | findings/DB query |
| `aov` | 160.990267 BRL (approx) | gmv_payments/order_count | findings |
| `median_order_value` | 105.29 BRL (approx) | order-level | findings |
| `repeat_customer_rate` | 3.1198% (2,997/96,096) | `customer_unique_id`, all statuses, observed period | findings/tests |
| `cancellation_rate` | 0.6285% (625/99,441) | status `canceled`, all orders denominator | findings/tests |
| `avg_review_score` | 4.086421 (n=99,224 valid review-order records) | `fact_reviews` valid 1–5, grain `(review_id,order_id)` | findings/tests |
| `on_time_delivery_rate` | 93.2258% (89,941/96,476) | delivered with estimate, `delivery_gap_days >= 0` | findings/tests |
| `avg_delivery_days` | 12.501046 days (n=96,478) | delivered with days | findings/tests |
| Geographic coverage | 99,441 orders, 16,008,872.12 BRL | `fact_orders` joined `staging.customers.customer_id` | validation/findings/notebook 04 |

**Baseline numerical comparison:** `backup/pre-remediation/` contains prior DB/findings/charts/validation artifacts; this reconciliation does not recompute a full historical baseline in-session. Where prior logic differed (e.g. geo mapping, review grain, correlation labeling, category review interpretation), current values reflect corrected methodology/definitions and should not be read as business performance change.

## 3. Pipeline Repeatability Evidence (isolated)

- **Environment:** copied `db/olist.duckdb` (141,307,904 bytes, 2026-11-14 10:41:40) to `db/olist_test_pipeline.duckdb` before tests; no parallel writers detected during run.
- **Run 1:** `python -m src.pipeline run --overwrite --db-path db/olist_test_pipeline.duckdb` → PASS (RC 0). Metrics: raw_orders 99,441; fact_orders 99,441; gmv 16,008,872.119999034; fact_reviews 99,224. Grain/analytics validation/integrity PASS. (Pre-fix behavior during run 1 wrote some default-path artifacts; main project artifacts were restored/regenerated afterward.)
- **Run 2:** same command repeated sequentially on same isolated DB → PASS (RC 0). Metrics: raw_orders 99,441; fact_orders 99,441; gmv 16,008,872.119999003; fact_reviews 99,224. No duplicate raw-table failure due to `--overwrite`.
- **Reconciliation:** key counts and KPI aggregates consistent between runs (minor floating-point representation difference only). Grain/transform/integrity validations PASS.
- **Main default DB:** full `pipeline run --overwrite` **NOT RUN** on `db/olist.duckdb` in this session (destructive ingest rebuild); default-DB stages/checks/exports were run and validated.

## 4. Interpretation Impact

- Correct geographic join and coverage restore confidence in regional comparisons and totals.
- Correct review grain and category/order-level review definition prevent overstated/ambiguous satisfaction claims.
- Explicit correlation methods and non-causal framing reduce analytical overclaim risk.
- Payment-based order value naming prevents confusion with merchandise-only GMV.
- Repeatability evidence supports technical credibility, with documented scope (isolated DB) and remaining default full-rerun not executed.

## 5. Remaining Gaps
- Live dataset license/terms verification pending.
- No repository software LICENSE declared (pending authorization).
- Default `db/olist.duckdb` not overwrite-rebuilt end-to-end in-session; isolated copy used for repeatability proof.
- Pipeline `validate` stage still writes raw DQ findings to default project path even when targeting isolated `--db-path` (analytics/integrity/export artifacts isolated after fix).
