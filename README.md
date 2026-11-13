# Olist Consumer Intelligence & Market Intelligence Assessment

Evidence-based consumer and marketplace intelligence analysis of the **Brazilian E-Commerce Public Dataset by Olist** (observed **2016-09-04 to 2018-10-17**, ~100k orders). Built as a reproducible portfolio project for market intelligence: clear business questions, approved KPI governance, validated pipeline, and decision-oriented recommendations.

**Source:** [Olist Brazilian E-Commerce Dataset (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | **Project:** OLIST-CI-02 | **Primary audience:** E-commerce marketplace management

---

## Business Problem

Marketplace teams need an integrated view of purchasing behavior, customer experience, category performance, and geographic operations. Transaction, item, payment, delivery, review, and customer data live in separate tables and must be reconciled at the correct grain before they can support reliable decisions.

**Research questions**
1. What patterns characterize consumer purchasing behavior?
2. How are delivery performance and freight costs associated with customer review scores?
3. How do purchasing patterns and review scores differ across product categories?
4. How do purchasing patterns and delivery performance vary by geographic region?

## Key Findings (approved KPIs)

*Metrics follow `docs/olist/03_kpi_definitions.md` v1.1 (source, `order_status` filter, and grain stated). Observational 2016–2018 data; associations, not causation.*

| Domain | Finding | Evidence (grain/filter) |
|---|---|---|
| Purchase behavior | **99,441 orders**, **~16.01M BRL GMV** (payments), **AOV ~160.99 BRL** (median ~105.29), avg **1.13 items/order** | `analytics.fact_orders`, all `order_status` |
| Retention & risk | **Repeat rate ~3.12%** (2,997/96,096 `customer_unique_id`); **cancellation rate ~0.63%** (625/99,441) | `staging.orders`+`staging.customers` linkage / `fact_orders`, all statuses |
| Delivery & experience | **On-time rate ~93.23%** (89,941/96,476); **avg delivery ~12.50 days** (n=96,478); **avg review ~4.09** (n=98,410) | `fact_delivery` + `fact_reviews`, delivered with required dates; valid reviews |
| Experience gap | On-time/early avg review **~4.29** (n=89,245) vs late **~2.27** (n=6,362); 30+ day bucket **~2.20** | Review joined to delivery (valid reviews). Spearman: delivery days vs review ~ -0.235 |
| Category mix | Revenue concentrated in `beleza_saude`, `relogios_presentes`, `cama_mesa_banho`, `esporte_lazer`, `informatica_acessorios` with varying avg reviews | `fact_order_items` (item grain) + review avg per order |
| Geography | GMV/orders concentrated in **SP/RJ/MG/RS/PR**; SP avg delivery **~8.7 days** vs several North/Northeast states **~20–29 days** | `fact_orders` joined `dim_customers` (state), delivered orders for delivery avg |

## Recommendations (prioritized)

1. **Protect delivery reliability (High, Ops/CX/Seller mgmt):** Reduce late deliveries and monitor on-time/lead-time buckets by lane/seller; late delivery aligns with materially lower reviews (association).
2. **Close regional SLA gaps (High, Ops/Marketplace):** Benchmark long-haul states/routes and target carrier/mode improvements while sustaining high-volume corridors.
3. **Category scorecards (Medium, Category/Commercial/CX):** Track GMV, orders, delivery, and review together; prioritize high-revenue, lower-review segments.
4. **Validate retention signal (Medium, Marketplace/CRM):** Low observed repeat (~3.12%) depends on `customer_unique_id` linkage and observed period; confirm identity before loyalty conclusions.
5. **Monitor cancellations explicitly (Medium, Ops):** Keep `canceled` distinct from `unavailable` in operational reporting (approved definition).

Details: [Executive summary](docs/executive_summary.md) · [Strategic recommendations](docs/strategic_recommendations.md)

## Visual Highlights

| Monthly order volume | Avg review by delivery time bucket | GMV by customer state (Top 15) |
|---|---|---|
| ![Monthly orders](docs/assets/monthly_orders.png) | ![Review by delivery bucket](docs/assets/review_by_delivery_bucket.png) | ![GMV by state](docs/assets/revenue_by_state.png) |

---

## Repository Guide

```text
olist-consumer-intelligence/
├── data/raw/                 # Source CSVs (gitignored)
├── db/                       # DuckDB warehouse (gitignored)
├── docs/                     # Charter, research design, KPI dict, data dictionary, architecture, DoD, reports, assets
├── notebooks/                # 00–05 analysis notebooks (executed, grain-aligned)
├── outputs/                  # Regenerable findings/charts/reports (gitignored by default)
├── queries/                  # SQL: 01_staging.sql, 02_analytics.sql
├── scripts/                  # Pipeline utilities and export
├── src/                      # ETL, validation, grain checks, config
├── tests/                    # Integrity/KPI tests
└── README.md
```

**Start here by audience:** [Portfolio audience guide](docs/portfolio_audience_guide.md) (30s / 5min / deep-dive paths).

## Reproducibility

**Prerequisites:** Python 3.11+, dependencies in `pyproject.toml` (`pip install -e .[dev]` or `pip install -r requirements-lock.txt` for a pinned environment snapshot), Kaggle Olist CSVs in `data/raw/` (see `src/config.py`). CI runs lint/format/type/test via `.github/workflows/ci.yml` (integrity tests skip when `db/` and `outputs/findings/` artifacts are not present).

```bash
# End-to-end pipeline (ingest -> validate -> transform -> grain-checks)
python -m src.pipeline run

# If raw tables already exist, run stages individually:
# python -m src.pipeline validate
# python -m src.pipeline transform
# python -m src.pipeline grain-checks

# Export findings/charts/reports
python scripts/export_analysis.py

# Quality checks
python -m pytest -q
python -m ruff check .
python -m black --check .
python -m mypy src --ignore-missing-imports
```

Notebooks in `notebooks/00–05` are executable top-to-bottom (set `PYTHONPATH` to project root when running outside an installed environment). Key artifacts: `docs/executive_summary.md`, `docs/strategic_recommendations.md`, `docs/assets/*.png`, and regenerable `outputs/findings/*`.

## Data Quality & Analytical Rigor

- **Pipeline:** `raw -> staging -> analytics` in DuckDB; raw data immutable; idempotent SQL transforms.
- **Validation:** Row/null/key/referential/range checks and grain/transform assertions (`outputs/findings/data_quality.json`, `docs/olist/analytics_validation.json`, `docs/olist/integrity_check.json`, `python -m src.pipeline grain-checks`).
- **Governance:** Approved KPI definitions and filters in `docs/olist/03_kpi_definitions.md`; every metric reported with source table, filter, and grain.
- **Known data notes:** Raw `reviews.review_id` not unique (deduplicated in analytics); `product_category_name` ~1.85% null; repeat behavior depends on `customer_unique_id` linkage and observed period. See `docs/olist/04_pitfalls.md`.

## Tech Stack

Python 3.11, DuckDB, SQL, pandas/NumPy, Matplotlib/Plotly/Seaborn, SciPy/statsmodels, Jupyter, pytest/ruff/black/mypy.

## Documentation

- [Project charter](docs/project_charter.md) · [Research design](docs/research_design.md) · [Data dictionary](docs/data_dictionary.md) · [System architecture](docs/system_architecture.md)
- [KPI definitions (approved)](docs/olist/03_kpi_definitions.md) · [Olist overview & schema](docs/olist/01_overview.md) · [Analysis pitfalls](docs/olist/04_pitfalls.md)
- [Definition of Done](docs/definition_of_done.md) · [Dataset license & attribution](docs/dataset_license_notes.md)

## Limitations & Ethics

- Observational marketplace sample (2016–2018); **not causal**, not representative of all Brazilian e-commerce or current conditions.
- `review_score` is a satisfaction proxy; response/coverage and timing biases possible. Category/state averages mask heterogeneity.
- Data is anonymized by the publisher; do not attempt re-identification. Verify dataset license/terms on Kaggle before public redistribution or commercial use and provide required attribution.

## Attribution

Dataset: *Brazilian E-Commerce Public Dataset by Olist* (Kaggle). Please cite Olist/Kaggle per the dataset page and review [docs/dataset_license_notes.md](docs/dataset_license_notes.md).
