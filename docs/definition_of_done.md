# Definition of Done (DoD)

**Project:** Olist Consumer Intelligence & Market Intelligence Assessment (OLIST-CI-02)  
**Version:** 1.0  
**Status:** Approved (project baseline)  
**Applies to:** Milestones, analysis deliverables, reports, and releases in this repository.

This document defines the criteria that must be satisfied before work is considered **Done**. Criteria align with project rules in `.roo/rules/`, the approved KPI dictionary (`docs/olist/03_kpi_definitions.md`), and professional reproducibility and governance practices.

---

## 1. Scope and Governance

- [ ] **Objective met:** The deliverable satisfies the stated milestone/task objective and acceptance criteria (see `docs/project_charter.md`, `docs/research_design.md`).
- [ ] **Single source of truth:** Metrics use approved definitions and filters from `docs/olist/03_kpi_definitions.md`. No silent invention or change of metric definitions; proposed changes are documented and approved before use.
- [ ] **Grain, source, filter stated:** Every reported number states source table(s), `order_status` filter (or applicable filter), and analytical grain.
- [ ] **Language and terminology:** Project artifacts (code, docs, identifiers, outputs) are in clear, consistent English. Original source categorical values are preserved; translations documented separately.

## 2. Data and Pipeline

- [ ] **Raw data immutable:** Data in `raw` schema/source files is not modified. Transformations occur only in staging/analytics via reproducible scripts/SQL.
- [ ] **Pipeline reproducible:** `python -m src.pipeline run` (or documented stages) completes successfully from expected inputs (`data/raw/` per `src/config.py`). Idempotent SQL/steps where applicable.
- [ ] **Data quality validated:** Row counts, nulls, key uniqueness, referential integrity, ranges, and reconciliation checks pass or have documented, accepted exceptions (`outputs/findings/data_quality.json`, validation artifacts).
- [ ] **Grain integrity verified:** Analytics fact/dimension grains and transform checks pass (`python -m src.pipeline grain-checks`, `docs/olist/analytics_validation.json`).
- [ ] **No hardcoded secrets/paths:** Configuration via code/config; no credentials committed; `.env` not committed.

## 3. Analysis and Outputs

- [ ] **Notebooks reproducible:** Analysis notebooks run top-to-bottom without errors in a clean environment (dependencies available, `PYTHONPATH`/working directory as documented) with outputs consistent with approved KPIs.
- [ ] **Artifacts regenerated:** Findings, charts, and reports are regenerated from the pipeline/database when definitions or logic change (`scripts/export_analysis.py`, `outputs/` as applicable).
- [ ] **Evidence-based interpretation:** Results distinguish correlation/association from causation; limitations, biases, and data-period constraints (2016–2018, observational) are stated.
- [ ] **Traceability:** Outputs can be traced to source tables, queries/scripts, and generation steps.

## 4. Quality and CI

- [ ] **Automated tests pass:** `python -m pytest -q` (and/or project test command) passes, including integrity/KPI checks relevant to the change.
- [ ] **Lint and format clean:** `ruff check .` and `black --check .` (or project-standard tools) pass for in-scope code.
- [ ] **Type checks clean:** `mypy src --ignore-missing-imports` (or project-standard configuration) passes, or deviations are documented and accepted.
- [ ] **No regressions:** Changes do not break existing validated metrics, grains, or reproducibility without an approved update to definitions/docs.

## 5. Documentation and Communication

- [ ] **Docs current:** `README.md`, research/design/data dictionary/architecture, and relevant `docs/` are updated to reflect behavior, status, and reproducibility steps.
- [ ] **Portfolio/readability:** Public-facing entry points are layered for intended audiences (summary, findings/recommendations, visuals, and deep-dive reproducibility). See `docs/portfolio_audience_guide.md`.
- [ ] **Assumptions and decisions recorded:** Filters, edge cases, and methodological choices are documented (comments, docs, or KPI dictionary notes).
- [ ] **References accurate:** Links, file paths, and artifact locations in documentation are valid.

## 6. Release and Hygiene

- [ ] **No sensitive or large prohibited artifacts committed:** Raw data, databases, secrets, and regenerable bulk outputs follow `.gitignore` and project policy; scratch/local files excluded.
- [ ] **License and attribution:** Dataset source, attribution, license/terms verification, and pre-publication checklist addressed (`docs/dataset_license_notes.md`); public outputs include period and limitations as required.
- [ ] **Version control:** Changes are committed in logical, reviewable units with clear messages; working tree is clean of unintended files.
- [ ] **Handoff readiness:** A reviewer or future contributor can reproduce results from documented steps and understand scope, limitations, and governance.

## 7. Sign-off

A deliverable is **Done** when all applicable items above are satisfied (or explicitly waived with documented rationale and approval). For major releases, record:

| Field | Value |
|---|---|
| Deliverable / milestone | |
| Date | |
| Verified by | |
| Evidence (commands/artifacts) | |
| Waivers / notes | |

---

**References:** `.roo/rules/00-olist-core.md`, `.roo/rules/01-data-standards.md`, `docs/project_charter.md`, `docs/research_design.md`, `docs/olist/03_kpi_definitions.md`, `docs/dataset_license_notes.md`, `docs/portfolio_audience_guide.md`, `README.md`.
