# Data Dictionary

**Project ID:** OLIST-CI-02
**Version:** 1.2
**Status:** Aligned to implemented schema/SQL and corrected grains (2026-11-14)

## 1. Source Data

- **Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle).
- **Observed order period:** 2016-09-04 21:15:19 to 2018-10-17 17:30:18 (`analytics.fact_orders.order_purchase_timestamp`).
- **Warehouse:** DuckDB `db/olist.duckdb` (default) with schemas `raw`, `staging`, `analytics`.
- **Raw inputs:** 9 CSVs in `data/raw/` (see `src/config.py`).

## 2. Schemas

### 2.1 Raw (`raw`)
Loaded via `read_csv_auto(..., header=true, all_varchar=true)` in `src/ingest.py` (source preserved as text).

| Table | Source file | Key / grain note |
|---|---|---|
| `orders` | `olist_orders_dataset.csv` | `order_id` |
| `order_items` | `olist_order_items_dataset.csv` | (`order_id`,`order_item_id`) |
| `customers` | `olist_customers_dataset.csv` | `customer_id` (order-scoped); includes `customer_unique_id` |
| `products` | `olist_products_dataset.csv` | `product_id` |
| `sellers` | `olist_sellers_dataset.csv` | `seller_id` |
| `payments` | `olist_order_payments_dataset.csv` | (`order_id`,`payment_sequential`) |
| `reviews` | `olist_order_reviews_dataset.csv` | `review_id` not unique in raw (duplicate IDs linked to different orders observed) |
| `geolocation` | `olist_geolocation_dataset.csv` | many rows per `geolocation_zip_code_prefix` |
| `category_translation` | `product_category_name_translation.csv` | `product_category_name` |

### 2.2 Staging (`staging`)
Typed/cleaned tables built by `queries/01_staging.sql`.
- Casts timestamps/numerics (TRY_CAST where appropriate), preserves source categorical values.
- `staging.geolocation` deduplicated by `geolocation_zip_code_prefix` (AVG lat/lng, representative city/state per prefix group as implemented).

### 2.3 Analytics (`analytics`)
Analysis-ready facts/dimensions built by `queries/02_analytics.sql`. Grains validated per `src/config.py`.

| Table | Type | Grain (key) | Description |
|---|---|---|---|
| `fact_orders` | Fact | 1 / `order_id` | Order attributes, status, timestamps, delivery metrics, payment-based totals, item count |
| `fact_order_items` | Fact | 1 / (`order_id`,`order_item_id`) | Item price/freight, product & seller attrs, freight ratio |
| `fact_payments` | Fact | 1 / (`order_id`,`payment_sequential`) | Payment details and installment metrics |
| `fact_reviews` | Fact | 1 / (`review_id`,`order_id`) | Review-order pairs with `valid_review_score`, order/customer/category link |
| `fact_delivery` | Fact | 1 / `order_id` | Delivery days/bucket/gap, freight/value shares, flags |
| `dim_customers` | Dimension | 1 / `customer_unique_id` | Location/identity aggregates over all linked orders; repeat flag |
| `dim_products` | Dimension | 1 / `product_id` | Attributes and sales aggregates |
| `dim_sellers` | Dimension | 1 / `seller_id` | Location and sales aggregates |

## 3. Key Analytics Columns (selected)

### `analytics.fact_orders`
`order_id`, `customer_id`, `customer_unique_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`, `order_purchase_year`, `order_purchase_month`, `order_purchase_day_of_week`, `is_delivered`, `delivery_time_days`, `delivery_gap_days`, `order_total_value` (sum of payments), `order_delivered_value` (item+freight aggregate as defined in SQL), `order_freight_value`, `order_items_count`.

### `analytics.fact_delivery`
`order_id`, `delivery_time_days`, `delivery_time_bucket` (`0-3 days`,`4-7 days`,`8-14 days`,`15-30 days`,`30+ days`), `delivery_gap_days` (estimated minus delivered; >= 0 treated as on-time/early per KPI), `order_estimated_delivery_date`, `order_delivered_customer_date`, `order_freight_value`, `order_total_value`, `freight_share`, `is_delivered`, `order_items_count`.

### `analytics.fact_reviews`
`review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`, `customer_id`, `product_category_name` (linked via order items as implemented), `valid_review_score` (1–5 or NULL).

### `analytics.dim_customers`
`customer_unique_id`, `customer_id` (deterministic representative), `customer_zip_code_prefix`, `customer_city`, `customer_state`, `total_orders`, `total_spent`, `avg_order_value`, `first_purchase_date`, `last_purchase_date`, `is_repeat_customer`.

## 4. Relationships and Join Guidance

- `fact_orders.customer_id` ↔ `staging.customers.customer_id` (use for order-level location/state analysis).
- `dim_customers.customer_unique_id` groups all linked orders for a unique customer; `dim_customers.customer_id` is a representative key, **not** a complete per-order mapping for geographic order analysis.
- `fact_orders.order_id` ↔ `fact_order_items.order_id` (1-to-many).
- `fact_orders.order_id` ↔ `fact_payments.order_id` (1-to-many).
- `fact_orders.order_id` ↔ `fact_reviews.order_id` (1-to-many at review-order grain).
- `fact_orders.order_id` ↔ `fact_delivery.order_id` (1-to-1).
- `fact_order_items.product_id` ↔ `dim_products.product_id`; `fact_order_items.seller_id` ↔ `dim_sellers.seller_id`.

## 5. Metric and Data Notes

- **Payment-based order value:** `gmv_payments`/`order_total_value` are payment-sum based (`SUM(payments.payment_value)`), not a pure item-merchandise-only GMV. Freight and payment composition are reflected as recorded in payments; state meaning explicitly in reports.
- **Repeat rate:** based on `customer_unique_id` linkage over observed period (approved KPI).
- **Review analyses:** use valid scores (1–5). Category review metric = avg order-level review among orders containing category at distinct `(order_id, category)`; do not interpret as item-level causal satisfaction.
- **Correlations:** computed as Pearson and Spearman separately on filtered samples (see exports/notebooks); associations only.

## 6. Data Quality and Integrity (validated)

- **DQ:** `outputs/findings/data_quality.json` (row/null/PK/referential/date/review-score checks).
- **Grain/transform:** `docs/olist/analytics_validation.json` (all checks PASS on current DB; geographic mapping reconciles 99,441 orders).
- **Integrity:** `docs/olist/integrity_check.json` (core raw referential checks PASS).
- **Known issues:** raw `reviews.review_id` duplicates exist (789 IDs linked to different orders; analytics preserves `(review_id,order_id)`); `products.product_category_name` null ~1.85%; boundary months 2016-09, 2018-09, 2018-10 partial and 2016-11 missing.

## 7. Reproducibility

- **Pipeline:** `python -m src.pipeline <command>` with optional `--db-path` and `--overwrite` for ingest/run (see `docs/system_architecture.md`).
- **SQL:** `queries/01_staging.sql`, `queries/02_analytics.sql`.
- **Exports/profiles:** `scripts/export_analysis.py`, `scripts/profile_olist.py`.
- **Tests:** `tests/test_pipeline_integrity.py` (DB-backed, skips if artifacts missing), `tests/test_unit_synthetic.py` (synthetic units).

## 8. Usage Rules

- Always state **source table(s), `order_status` filter, and grain** with each metric.
- Avoid fanout: aggregate at intended grain before interpretation (e.g. distinct orders/customers/order-category pairs).
- Treat findings as observational (2016–2018 sample); no causal claims.
