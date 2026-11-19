# One-page summary: Olist Consumer & Marketplace Intelligence

**Question:** Does delivery speed relate to customer satisfaction on the Olist marketplace?

**Data:** Brazilian Olist E-Commerce dataset (Kaggle, CC BY-NC-SA 4.0), observed 2016-09-04 to 2018-10-17 — 99,441 orders, with order, item, payment, delivery, review, and customer location data. This is an **observational** study: it shows associations, not cause and effect. The original dataset is not redistributed in this repository.

## Approach in three steps

1. **Reconcile at the right grain.** Join orders, items, payments, deliveries, reviews, and customer location so each order and each review-order pair is counted once — no double counting.
2. **Use governed metrics.** Every figure follows a single approved KPI dictionary (`docs/olist/03_kpi_definitions.md`) stating its source table, `order_status` filter, and grain.
3. **Validate and chart.** Run grain and transform checks, then chart delivery buckets vs review scores and GMV by customer state. Pipeline, lint, format, type, and test checks are all automated.

## Headline results

- **99,441 orders** and **~16.01M BRL** gross merchandise value (payments).
- **160.99 BRL** average order value (median 105.29 BRL).
- **93.23% on-time delivery rate** (derived late share: 6.77% = 100% minus the on-time rate).
- **Satisfaction gap:** on-time/early orders average 4.29 stars vs 2.27 stars for late deliveries (association, not causation; relative to the estimated delivery date — a different cut from delivery-duration buckets).
- **Delivery varies by state:** 8.3 days in São Paulo (SP) vs 19–24+ days in several North/Northeast states.
- **3.12% repeat customer rate** in the observed period.

## What it suggests

Delivery reliability is the most promising area to investigate or test; the data show associations, not causes. Regional SLA gaps and category scorecards are secondary priorities. Low repeat purchasing (3.12%) should be confirmed against customer identity linkage before loyalty conclusions.

## Limits

- Observational 2016–2018 sample; not causal, not representative of all Brazilian e-commerce or current conditions.
- Review score is a satisfaction proxy; response and timing bias possible.
- Category and state averages mask heterogeneity; monthly endpoints are partially observed.
- Data is anonymized by the publisher; do not attempt re-identification.

## How to reproduce

1. `pip install -e .[dev]`
2. Place the Kaggle Olist CSVs in `data/raw/` (see `src/config.py`).
3. `python -m src.pipeline export` (reads the database and regenerates findings and charts).
4. `python -m pytest -q` (optional real-dataset tests may be skipped).
5. `python -m ruff check .`, `python -m black --check .`, `python -m mypy src --ignore-missing-imports`.

Full detail: [executive_summary.md](executive_summary.md) · [strategic_recommendations.md](strategic_recommendations.md)

Dataset attribution: Brazilian E-Commerce Public Dataset by Olist, CC BY-NC-SA 4.0 (listing verified 2026-11-14). Legal interpretation for this portfolio/job-application use is not independently resolved. No project source-code license is granted yet (no `LICENSE` file).
