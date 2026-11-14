# Definition of Done (DoD)

**Project:** Olist Consumer Intelligence & Market Intelligence Assessment (OLIST-CI-02)
**Version:** 1.1
**Status:** Evidence-based update (branch `fix/olist-analytical-integrity`, 2026-11-14) — not fully signed off for public release
**Applies to:** Milestones, analysis deliverables, reports, and releases in this repository.

Criteria align with project rules, approved KPI dictionary (`docs/olist/03_kpi_definitions.md`), and reproducibility/governance practices. Items marked complete require evidence.

---

## 1. Scope and Governance

- [x] **Objective (remediation scope):** Correct analytical integrity (grains/joins/KPIs/SQL/pipeline/exports/tests/notebooks/docs) and improve reproducibility on existing branch. Evidence: corrected SQL/src/scripts/tests/docs, validation artifacts, reconciliation doc.
- [x] **Single source of truth:** Metrics aligned to `docs/olist/03_kpi_definitions.md` v1.1; `gmv_payments` documented as payment-based order value. Evidence: findings/reports/docs updated.
- [x] **Grain, source, filter stated:** Major outputs/reporting updated to state grain/filter/method where applicable. Evidence: exports, reports, notebooks, reconciliation.
- [x] **Language and terminology:** Project artifacts maintained in clear English; original source categorical values preserved.

## 2. Data and Pipeline

- [x] **Raw data immutable:** No modifications to `data/raw/` CSVs; transforms in staging/analytics via SQL/scripts.
- [~] **Pipeline reproducible:** Stages and isolated full rebuild tested. Evidence: `python -m src.pipeline run --overwrite --db-path db/olist_test_pipeline.duckdb` PASS twice sequentially (isolated copy) with consistent core metrics; default-DB grain/analytics/integrity/export checks PASS. **Gap:** full `pipeline run --overwrite` not executed on default `db/olist.duckdb` in-session (destructive rebuild avoided).
- [x] **Data quality validated:** Raw DQ, grain, transform, referential checks PASS. Evidence: `outputs/findings/data_quality.json`, `docs/olist/analytics_validation.json`, `docs/olist/integrity_check.json`.
- [x] **Grain integrity verified:** Analytics grains/keys/reconciliations PASS (`python -m src.pipeline grain-checks`, analytics validation). Evidence: validation JSON, tests.
- [x] **No hardcoded secrets/paths:** Config-driven paths; no credentials committed observed.

## 3. Analysis and Outputs

- [~] **Notebooks reproducible/executed:** `notebooks/00-05` executed top-to-bottom in this environment via `jupyter nbconvert --execute` with `PYTHONPATH` and bootstrap cell (2026-11-14), exit codes 0 and outputs present. **Note:** nbformat MissingIDField warnings and benign ZMQ teardown assertion messages appeared in stderr for some runs; environment-specific.
- [x] **Artifacts regenerated:** Findings/CSVs/charts/docs assets and reports regenerated on default DB. Evidence: `scripts/export_analysis.py` output, timestamps, `outputs/findings/*`, `docs/assets/*`.
- [x] **Evidence-based interpretation:** Associations/correlation wording, observational limitations, and grain caveats documented in reports/notebooks/docs.
- [x] **Traceability:** Outputs traceable to SQL (`queries/`), pipeline/scripts (`src/`, `scripts/`), and validation artifacts.

## 4. Quality and CI

- [x] **Automated tests pass (current local run):** `python -m pytest -q` â†’ **10 passed, 3 skipped, 0 failed** (synthetic/temporary tests + DB-backed checks where artifacts available; 3 real-dataset acceptance tests skipped unless `OLIST_RUN_REAL_DATASET_TESTS=1` with required local artifacts).
- [x] **Lint and format clean:** `python -m ruff check .` PASS; `python -m black --check .` PASS (CI parity); `python -m mypy src --ignore-missing-imports` PASS in this session.
- [x] **No regressions observed:** Corrected metrics/grains reconciled; validations/tests pass. Re-run gates after any further code/doc changes.

## 5. Documentation and Communication

- [~] **Docs current:** `system_architecture.md`, `data_dictionary.md`, `olist/04_pitfalls.md`, `dataset_license_notes.md`, `definition_of_done.md`, `remediation_reconciliation.md` updated/aligned; KPI/research/charter/README/reports reviewed for consistency. **Gap:** legal interpretation of intended portfolio/use context and project source-code license decision remain pending owner authorization (dataset listing license verified on Kaggle 2026-11-14).
- [x] **Portfolio/readability:** README, executive summary, strategic recommendations, visuals, and audience guide present.
- [x] **Assumptions and decisions recorded:** KPI dictionary, pitfalls, reconciliation, and pipeline semantics documented.
- [~] **References accurate:** Core paths/commands updated; validate against any future structural changes.

## 6. Release and Hygiene

- [x] **No sensitive/large prohibited artifacts committed (current review):** `.gitignore` excludes `data/raw/`, `db/`, `outputs/`, `.env*`, caches/scratch; no secrets found. Untracked `backup/` and `db/olist_test_pipeline.duckdb` exist locally and must **not** be committed.
- [~] **License and attribution:** Dataset listing license verified on Kaggle (2026-11-14, CC BY-NC-SA 4.0) and documented with attribution/period/limitations; **legal interpretation of intended use is not independently resolved**; **project source-code license not declared** (no LICENSE committed; decision pending owner authorization).
- [ ] **Version control (curated commit):** Working tree contains many modified/untracked files; no staging/commit performed (explicit authorization required).
- [~] **Handoff readiness:** Repro steps and evidence documented; remaining blockers/uncertainties explicitly listed.

## 7. Sign-off

A deliverable is **Done** when all applicable items above are satisfied (or explicitly waived with documented rationale and approval).

| Field | Value |
|---|---|
| Deliverable / milestone | Remediation finalization (analytical integrity, reproducibility evidence, docs alignment) |
| Date | 2026-11-14 |
| Verified by | Automated checks + in-session execution evidence (not human release sign-off) |
| Evidence (commands/artifacts) | `ruff check .` PASS; `black --check .` PASS (CI parity); `mypy src --ignore-missing-imports` PASS; `pytest -q` 10 passed, 3 skipped (3 real-dataset acceptance tests optional); notebooks 00-05 executed earlier (nbconvert RC 0) and not materially changed; `pipeline grain-checks/analytics-validate/integrity` PASS on default DB; isolated `pipeline run --overwrite --db-path db/olist_test_pipeline.duckdb` PASS twice; real-data cold-start+repeat on temp DB PASS twice; `docs/olist/remediation_reconciliation.md` |
| Waivers / notes | Default full `pipeline run --overwrite` not run on main DB; legal interpretation of intended use unresolved; project source-code license unspecified; no commit/push |
