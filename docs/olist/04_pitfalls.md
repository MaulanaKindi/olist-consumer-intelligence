# Olist: Analysis Pitfalls and Project Handling

These points reflect common characteristics of the Olist dataset. In this project they were checked against the data and handled as noted (see profiles, validation, and analytics SQL).

| Pitfall | Project handling / verification |
|---|---|
| Joining orders to order_items duplicates rows per item | Order counts/revenue computed at correct grain (`COUNT(DISTINCT order_id)` where needed); item-level metrics kept at item grain; review aggregated per order before joining to items to avoid fanout |
| Geolocation has many rows per `zip_code_prefix` | Deduplicated in `staging.geolocation` (avg lat/lng, grouped by prefix) |
| `customer_id` is order-scoped; cross-order identity uses another key | `customer_unique_id` exists and is used for repeat-customer analysis (linkage validated in staging/analytics queries) |
| One order can have several payment rows and/or multiple reviews | Payments aggregated per order for order totals; raw `review_id` duplicates handled by deduplication in `analytics.fact_reviews` (1 row/review_id) |
| Product category translation table may exist separately | `product_category_name_translation` ingested and available; original category values preserved |
| `order_status` distribution matters for metrics | Status distribution checked; approved KPI filters defined in `docs/olist/03_kpi_definitions.md` (default all statuses, with explicit delivery/review constraints where specified) |

**Rule:** State source table, `order_status` filter, and grain for every reported metric. Re-verify assumptions with queries when extending the analysis.
