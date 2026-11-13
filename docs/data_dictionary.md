# Data Dictionary

**Project ID:** OLIST-CI-02  
**Version:** 1.1  
**Status:** Finalized (aligned to implemented analytics schema)

## 1. Source Data

- **Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle).  
- **Observed order period:** 2016-09-04 21:15:19 to 2018-10-17 17:30:18 (`raw.orders.order_purchase_timestamp` / `analytics.fact_orders.order_purchase_timestamp`).  
- **Warehouse:** DuckDB `db/olist.duckdb` with schemas `raw`, `staging`, `analytics`.

## 2. Schemas

### 2.1 Raw (`raw`)
Ingested as VARCHAR via `read_csv_auto(..., all_varchar=true)`; source of truth preserved.

| Table | Key / Grain (source) | Notes |
|-------|-----------------------|------|
| `orders` | `order_id` | Timestamps, status |
| `order_items` | `order_id`, `order_item_id` | Price, freight |
| `customers` | `customer_id` | Includes `customer_unique_id` |
| `products` | `product_id` | Category and attributes |
| `sellers` | `seller_id` | Location |
| `payments` | `order_id`, `payment_sequential` | Payment rows |
| `reviews` | `review_id` (not unique in raw) | Score/comments/timestamps; duplicates exist |
| `geolocation` | `geolocation_zip_code_prefix` (many rows/prefix) | Lat/lng/city/state |
| `category_translation` | `product_category_name` | PT→EN mapping |

### 2.2 Staging (`staging`)
Typed/cleaned equivalents of raw tables (timestamps, numeric casts). `staging.geolocation` is deduplicated by `geolocation_zip_code_prefix` (avg lat/lng). See `queries/01_staging.sql`.

### 2.3 Analytics (`analytics`)
Analysis-ready facts/dimensions. See `queries/02_analytics.sql`.

| Table | Type | Grain (key) | Description |
|-------|------|-------------|-------------|
| `fact_orders` | Fact | 1 / `order_id` | Order attributes, time parts, delivery metrics, totals |
| `fact_order_items` | Fact | 1 / (`order_id`,`order_item_id`) | Item price/freight, product & seller attrs, `freight_to_price_ratio` |
| `fact_payments` | Fact | 1 / (`order_id`,`payment_sequential`) | Payment details, `avg_installment_value`, links |
| `fact_reviews` | Fact | 1 / `review_id` | Deduplicated reviews with `valid_review_score`, order/customer/category link |
| `fact_delivery` | Fact | 1 / `order_id` | Delivery days/bucket/gap, freight/value shares, status flags |
| `dim_customers` | Dimension | 1 / `customer_unique_id` | Location, aggregated orders/spend, repeat flag |
| `dim_products` | Dimension | 1 / `product_id` | Attributes and sales aggregates |
| `dim_sellers` | Dimension | 1 / `seller_id` | Location and sales aggregates |

## 3. Key Analytics Columns (selected)

### `analytics.fact_orders`
`order_id`, `customer_id`, `customer_unique_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_customer_date`, `order_estimated_delivery_date`, `order_purchase_year`, `order_purchase_month`, `order_purchase_day_of_week`, `is_delivered`, `delivery_time_days`, `delivery_gap_days`, `order_total_value`, `order_delivered_value`, `order_freight_value`, `order_items_count`.

### `analytics.fact_delivery`
`order_id`, `delivery_time_days`, `delivery_time_bucket`, `delivery_gap_days`, `order_estimated_delivery_date`, `order_delivered_customer_date`, `order_freight_value`, `order_total_value`, `freight_share`, `is_delivered`, `order_items_count`.

### `analytics.fact_reviews`
`review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`, `customer_id`, `product_category_name`, `valid_review_score`.

### `analytics.dim_customers`
`customer_unique_id`, `customer_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state`, `total_orders`, `total_spent`, `avg_order_value`, `first_purchase_date`, `last_purchase_date`, `is_repeat_customer`.

## 4. Relationships (analytics)

- `dim_customers.customer_id` ↔ `fact_orders.customer_id` (orders placed; customer dimension keyed by `customer_unique_id`)
- `fact_orders.order_id` ↔ `fact_order_items.order_id`
- `fact_orders.order_id` ↔ `fact_payments.order_id`
- `fact_orders.order_id` ↔ `fact_reviews.order_id`
- `fact_orders.order_id` ↔ `fact_delivery.order_id`
- `fact_order_items.product_id` ↔ `dim_products.product_id`
- `fact_order_items.seller_id` ↔ `dim_sellers.seller_id`

Geographic analysis joins `fact_orders` to `dim_customers` on `customer_id` to use `customer_state`.

## 5. Data Quality and Integrity

- **DQ findings:** `outputs/findings/data_quality.json` (refreshed via pipeline/validation). Core referential integrity checks pass (0 orphaned on validated links). `review_score` values in range 1–5 where present.
- **Analytics validation:** `docs/olist/analytics_validation.json` (grain and transform checks all valid).
- **Known issues:** raw `reviews.review_id` not unique (deduplicated in `fact_reviews`); `products.product_category_name` null rate ~1.85%.

## 6. Processing and Reproducibility

- **Ingest/validate/transform/grain:** `python -m src.pipeline run` (requires `data/raw/`).  
- **SQL definitions:** `queries/01_staging.sql`, `queries/02_analytics.sql`.  
- **Analysis exports:** `python scripts/export_analysis.py` → `outputs/findings/*`, `outputs/charts/*`.  
- **Profiles:** `docs/olist/profile/*.md` (generated by `scripts/profile_olist.py`).

## 7. Usage Notes

- State **source table, `order_status` filter, and grain** with every reported metric.  
- Joining orders to items multiplies rows; aggregate at intended grain (e.g. `COUNT(DISTINCT order_id)`).  
- Original categorical values (e.g. Portuguese `product_category_name`) are preserved; translations are separate/reference data.  
- Candidate/approved KPI definitions are governed by `docs/olist/03_kpi_definitions.md`.
