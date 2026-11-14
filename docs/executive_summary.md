# Executive Intelligence Report

**Project:** Olist Consumer Intelligence & Market Intelligence Assessment (OLIST-CI-02)  
**Data period:** 2016-09-04 to 2018-10-17 (orders.purchase timestamp, observed)  
**Generated from:** `db/olist.duckdb` (`raw`/`staging`/`analytics`), `outputs/findings/analysis_findings.json`  
**KPI governance:** `docs/olist/03_kpi_definitions.md` v1.1 (approved). Metrics reported with source, filter, and grain.

## Scope and method
- **Sources/grains:** `analytics.fact_orders` (1/order), `analytics.fact_delivery` (1/order), `analytics.fact_order_items` (1/order-item), `analytics.fact_reviews` (1/review_id, 1/order pair; 99,224 review-order records, 98,410 review_ids, all valid scores 1–5 in observed data), repeat linkage via `staging.orders`+`staging.customers` on `customer_unique_id`.
- **Default filter:** all `order_status` for volume/value/repeat/cancellation KPIs unless stated. Delivery/review KPIs apply approved constraints (delivered with required dates; valid review scores).
- **Design:** observational, descriptive/diagnostic. Associations are not causal.

## Data quality highlights
- Core volumes (raw): orders 99,441; order_items 112,650; customers 99,441; payments 103,886; reviews 99,224. Referential integrity on validated core links: orphaned = 0. Analytics grain/transform checks: PASS.
- Notes: raw `reviews.review_id` has 789 duplicate IDs, each associated with a different `order_id` (same review content/score/timestamps observed). Analytics preserves review-order pairs (grain `review_id, order_id`) with deterministic deduplication of exact review-order rows. `products.product_category_name` null ~1.85%. Monthly coverage includes partial boundary months (2016-09, 2018-09, 2018-10) and missing 2016-11.

## Key findings (approved KPIs)

### 1. Consumer purchase behavior (order/customer grain, all statuses)
- `order_count`: 99,441; `gmv_payments` (payment-based order value): ~16,008,872 BRL; `aov`: ~160.99 BRL; median order value ~105.29 BRL; avg items/order ~1.13.
- `repeat_customer_rate`: ~3.12% (2,997 of 96,096 `customer_unique_id`, observed period). `cancellation_rate`: ~0.63% (625/99,441, `order_status='canceled'`).
- Status mix dominated by delivered (~96,478); other statuses present (shipped, unavailable, etc.). Trend interpretation must account for incomplete boundary months.

### 2. Experience intelligence (review-order + delivery/order grain)
- `avg_review_score` (valid 1–5): ~4.086 (n=99,224 review-order records with valid score).
- `avg_delivery_days` (delivered with days): ~12.50 days (n=96,478). `on_time_delivery_rate` (delivered with estimate, gap >= 0): ~93.23% (89,941/96,476).
- On-time/early avg review ~4.290 (n=89,949) vs late ~2.271 (n=6,410). Delivery buckets (chronological) show gradient: 0–3 days ~4.464 (n=6,951), 4–7 ~4.397 (n=23,730), 8–14 ~4.298 (n=37,986), 15–30 ~3.940 (n=23,485), 30+ ~2.204 (n=4,207).
- Correlations on delivered orders with valid reviews (pandas): Pearson(delivery_time_days, review)=~-0.334, Spearman(delivery_time_days, review)=~-0.235; Pearson/Spearman(delivery_gap_days, review)=~+0.267/+0.176; freight associations weaker. Associations only.

### 3. Product & category intelligence (item grain; review at distinct order-category grain)
- Revenue concentrates in categories such as beleza_saude, relogios_presentes, cama_mesa_banho, esporte_lazer, informatica_acessorios (`outputs/findings/category_performance.csv`).
- Category review metric: average order-level review among orders containing the category (distinct `order_id, category` pairs; an order may contribute to multiple categories). This is not a product-level causal satisfaction measure.

### 4. Geographic intelligence (order-level location via `staging.customers.customer_id`)
- Geographic mapping covers all orders (99,441) and reconciles to total GMV (~16,008,872 BRL).
- GMV/orders concentrate in SP, RJ, MG, RS, PR (e.g. SP: 41,746 orders, ~5.998M BRL). Avg delivery days lower in SP (~8.3) and higher in several North/Northeast states (often ~19–24+ days) (`outputs/findings/state_performance.csv`).

## Decision implications (evidence-based)
- **CX/Operations:** Protect and improve on-time delivery; late/long-haul deliveries align with materially lower reviews.
- **Logistics/Regional:** Target SLA and lane improvements in high-delay states while sustaining high-volume corridors.
- **Category/Commercial:** Pair revenue with satisfaction in category scorecards using order-category review interpretation; act on high-revenue lower-review segments.
- **Retention:** Low observed repeat rate (~3.12%) suggests limited repeat behavior in-period under current identity linkage; validate linkage before loyalty conclusions.

## Limitations
- Observational 2016–2018 sample; no causal claims or market-wide inference.
- Review score is a satisfaction proxy; response/coverage bias possible. Duplicate `review_id` records linked to different orders are preserved as review-order pairs.
- State/category averages mask heterogeneity; boundary months are incomplete; follow approved filters for recomputation.

## Reproducibility
- Pipeline: `python -m src.pipeline run --overwrite` (with `data/raw/`) or stage commands; analytics validation and integrity checks included in pipeline flow.
- Exports: `python scripts/export_analysis.py`. Tests: `python -m pytest -q`. Quality: `ruff check .`, `black --check .`, `mypy src --ignore-missing-imports`.
- Artifacts: `outputs/findings/*`, `outputs/charts/*`, `outputs/reports/*`, `docs/olist/analytics_validation.json`, `docs/olist/integrity_check.json`.
