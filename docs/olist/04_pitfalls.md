# Olist: Analysis Pitfalls and Project Handling

These points reflect common characteristics of the Olist dataset and how this project handles them (verified in SQL, pipeline checks, exports, and notebooks where executed).

| Pitfall | Project handling / verification |
|---|---|
| Joining orders to order_items duplicates rows per item | Order counts/revenue computed at correct grain (`COUNT(DISTINCT order_id)` where needed); item metrics kept at item grain; review/category analyses aggregated to intended grain to avoid fanout. |
| Geolocation has many rows per `zip_code_prefix` | Deduplicated in `staging.geolocation` (avg lat/lng and representative city/state per prefix as implemented in `queries/01_staging.sql`). |
| `customer_id` is order-scoped; cross-order identity uses `customer_unique_id` | Repeat behavior uses `customer_unique_id` via `staging.orders`/`staging.customers` linkage (approved KPI). |
| Order-level geography can be wrong if joined through representative customer dimension keyed by `customer_unique_id` | Order-level state analysis joins `analytics.fact_orders` to `staging.customers` on `customer_id` (reconciled to 99,441 orders / ~16,008,872.12 BRL in validation/exports). `dim_customers` remains 1 row per `customer_unique_id` for customer-level aggregates. |
| One order can have several payment rows and/or multiple reviews | Payments aggregated per order for payment-based order value; raw `reviews.review_id` is not globally unique as a standalone key (duplicate IDs linked to different orders observed). `analytics.fact_reviews` uses grain `(review_id, order_id)` and deterministic dedup of exact review-order rows (99,224 review-order records, 98,410 distinct review_ids). |
| Category-level review interpretation can be misleading | Category review metric defined as average order-level review among orders containing the category at distinct `(order_id, category)`; not item-weighted and not causal product-satisfaction. |
| Pearson/Spearman method confusion | `corr()` in DuckDB/SQL contexts must not be mislabeled as Spearman; exports/notebooks compute Pearson and Spearman explicitly via pandas (`method='pearson'` / `method='spearman'`) and report both. |
| `order_status` distribution matters for metrics | Approved KPI filters defined in `docs/olist/03_kpi_definitions.md` v1.1 (default all statuses with explicit delivery/review constraints). |
| Monthly boundaries and missing months | Exports use complete month spine and mark partial boundary months (2016-09, 2018-09, 2018-10) and missing 2016-11; do not treat endpoints as comparable full months. |
| Product category translation table exists separately | `product_category_name_translation` ingested/available; original category values preserved. |

**Rule:** State source table, `order_status` filter, and grain for every reported metric. Re-verify assumptions with queries when extending the analysis.
