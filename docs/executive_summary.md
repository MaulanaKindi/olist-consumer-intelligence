# Executive Intelligence Report

**Project:** Olist Consumer Intelligence & Market Intelligence Assessment (OLIST-CI-02)  
**Data period:** 2016-09-04 to 2018-10-17 (orders.purchase timestamp, observed)  
**Generated from:** `db/olist.duckdb` (`raw`/`staging`/`analytics`), `outputs/findings/analysis_findings.json`  
**KPI governance:** `docs/olist/03_kpi_definitions.md` v1.1 (approved). Metrics reported with source, filter, and grain.

## Scope and method
- **Sources/grains:** `analytics.fact_orders` (1/order), `analytics.fact_delivery` (1/order), `analytics.fact_order_items` (1/order-item), `analytics.fact_reviews` (1/review_id, deduplicated), repeat linkage via `staging.orders`+`staging.customers` on `customer_unique_id`.
- **Default filter:** all `order_status` for volume/value/repeat/cancellation KPIs unless stated. Delivery/review KPIs apply approved constraints (delivered with required dates; valid review scores).
- **Design:** observational, descriptive/diagnostic. Associations are not causal.

## Data quality highlights
- Core volumes (raw): orders 99,441; order_items 112,650; customers 99,441; payments 103,886; reviews 99,224. Referential integrity on validated core links: orphaned = 0. Analytics grain/transform checks: PASS.
- Notes: raw `reviews.review_id` not unique (deduplicated in analytics); `products.product_category_name` null ~1.85%.

## Key findings (approved KPIs)

### 1. Consumer purchase behavior (order/customer grain, all statuses)
- `order_count`: 99,441; `gmv_payments`: ~16,008,872 BRL; `aov`: ~160.99 BRL; median order value ~105.29 BRL; avg items/order ~1.13.
- `repeat_customer_rate`: ~3.12% (2,997 of 96,096 `customer_unique_id`, observed period). `cancellation_rate`: ~0.63% (625/99,441, `order_status='canceled'`).
- Status mix dominated by delivered (~96,478); other statuses present (shipped, unavailable, etc.).

### 2. Experience intelligence (review + delivery/order grain)
- `avg_review_score` (valid 1–5): ~4.089 (n=98,410 reviews).
- `avg_delivery_days` (delivered with days): ~12.50 days (n=96,478). `on_time_delivery_rate` (delivered with estimate, gap >= 0): ~93.23% (89,941/96,476).
- On-time/early avg review ~4.29 (n=89,245) vs late ~2.27 (n=6,362). Delivery buckets show gradient (e.g. 0–3 days ~4.46, 30+ days ~2.20). Spearman associations (delivered, valid reviews): delivery_time_days negative with review, gap positive; freight weaker.

### 3. Product & category intelligence (item grain, review averaged per order)
- Revenue concentrates in categories such as beleza_saude, relogios_presentes, cama_mesa_banho, esporte_lazer, informatica_acessorios (`outputs/findings/category_performance.csv`). Average review varies by category; comparisons preserve item/order grain and per-order review aggregation.

### 4. Geographic intelligence (order grain joined to customer state)
- GMV/orders concentrate in SP, RJ, MG, RS, PR. Avg delivery days lower in SP (~8.7) and higher in several North/Northeast states (often ~20+ days) (`outputs/findings/state_performance.csv`).

## Decision implications (evidence-based)
- **CX/Operations:** Protect and improve on-time delivery; late/long-haul deliveries align with materially lower reviews.
- **Logistics/Regional:** Target SLA and lane improvements in high-delay states while sustaining high-volume corridors.
- **Category/Commercial:** Pair revenue with satisfaction in category scorecards; prioritize high-revenue lower-review segments.
- **Retention:** Low observed repeat rate (~3.12%) suggests limited repeat behavior in-period under current identity linkage; validate linkage before loyalty conclusions.

## Limitations
- Observational 2016–2018 sample; no causal claims or market-wide inference.
- Review score is a proxy; response/coverage bias possible. Identity linkage affects repeat measurement.
- State/category averages mask heterogeneity; follow approved filters for any recomputation.

## Reproducibility
- Pipeline: `python -m src.pipeline run` (with `data/raw/`). Exports: `python scripts/export_analysis.py`.
- Artifacts: `outputs/findings/*`, `outputs/charts/*`, `outputs/reports/*`, `docs/olist/analytics_validation.json`.
