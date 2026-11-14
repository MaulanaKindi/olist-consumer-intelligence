# Olist: KPI Definitions (KPI Dictionary)

Status: FINALIZED (approved set v1.1 for analysis/reports in this repo). Every metric below marked APPROVED is the authoritative definition for project outputs unless superseded by a newer approved version.
Rules:
- Do not invent or change a metric definition silently. Propose changes and wait for approval.
- Map "Source columns" from docs/olist/profile/<schema>.<table>.md and analytics schema. Never guess column names.
- Every metric states its grain, filters, and time basis.
- Always report: source table(s), `order_status` filter, and grain.

## Business questions
1. How do customers purchase and repeat on the marketplace? (volume, value, repeat behavior)
2. How are delivery and freight associated with observed review scores?
3. How do performance and experience differ by product category and customer state?

## Approved metrics

| Name | Business question | Definition | Grain | Source tables / columns | Filters | Time basis | Edge cases | Status |
|---|---|---|---|---|---|---|---|---|
| order_count | 1 | `COUNT(DISTINCT order_id)` | Order-level aggregate (report overall/month/state/etc.) | `analytics.fact_orders.order_id` | **All `order_status` values** unless a metric explicitly states otherwise | `order_purchase_timestamp` (UTC as stored) | Do not `COUNT(*)` after joining `fact_order_items`/payments/reviews | APPROVED |
| gmv_payments | 1 | `SUM(order_total_value)` where `order_total_value` is the sum of payments per order | Order-level aggregate | `analytics.fact_orders.order_total_value`, `analytics.fact_payments.payment_value` (source of total) | **All `order_status` values** | `order_purchase_timestamp` | Includes all payment types/installments as recorded; includes freight component present in payments | APPROVED |
| aov | 1 | `gmv_payments / order_count` over same population | Order-level aggregate | `analytics.fact_orders.order_total_value`, `order_id` | **All `order_status` values** | `order_purchase_timestamp` | Numerator/denominator must use identical filters | APPROVED |
| repeat_customer_rate | 1 | `repeat_customers / total_customers` where repeat means `COUNT(DISTINCT order_id) > 1` per `customer_unique_id` | Customer (`customer_unique_id`) | `analytics.fact_orders.customer_unique_id`, `order_id` | **All `order_status` values** (observed purchase behavior) | Based on orders in observed period | Depends on identity linkage quality of `customer_unique_id`; observed-period only | APPROVED |
| avg_review_score | 2,3 | `AVG(valid_review_score)` over valid **review-order records** (each `(review_id, order_id)` pair weighted equally) | Review-order pair (1/`review_id,order_id`) or aggregated as stated | `analytics.fact_reviews.valid_review_score`, `review_id`, `order_id` | `valid_review_score IS NOT NULL` (scores 1–5); order `order_status` = **all** unless noted | `review_creation_date` / `review_answer_timestamp` as available (reporting uses review record, not purchase time) | `analytics.fact_reviews` preserves review-order pairs (99,224 valid records, 98,410 distinct `review_id`; 789 repeated ID groups / 814 excess occurrences in current data). Repeated IDs have identical score/content in observed diagnostics but source semantics unresolved; do not call records "unique customer reviews". Primary metric = mean per valid review-order record; distinct `review_id` count may be reported separately. When combining with items, aggregate to intended grain (e.g. per `order_id` or distinct `order_id, category`) to avoid fanout. | APPROVED |
| on_time_delivery_rate | 2,4 | `delivered_on_time_or_early / delivered_with_estimate` where on-time/early means `delivery_gap_days >= 0` | Order (delivered) | `analytics.fact_delivery.delivery_gap_days`, `order_id`, `is_delivered`, `analytics.fact_orders.order_status` | **`is_delivered = TRUE` AND `delivery_gap_days IS NOT NULL`** (requires actual & estimated delivery dates); effectively delivered orders | Delivery outcome dates (`order_delivered_customer_date`, `order_estimated_delivery_date`) | Excludes undelivered/unestimated orders; `delivery_gap_days = estimated - delivered` (positive = early) | APPROVED |
| avg_delivery_days | 2,4 | `AVG(delivery_time_days)` | Order (delivered) | `analytics.fact_delivery.delivery_time_days`, `analytics.fact_orders.is_delivered` | **`is_delivered = TRUE` AND `delivery_time_days IS NOT NULL`** | `order_purchase_timestamp` to `order_delivered_customer_date` | Excludes not-yet-delivered/canceled-without-delivery; outliers retained unless separately stated | APPROVED |
| cancellation_rate | 1 | `canceled_orders / order_count_all` where canceled means `order_status = 'canceled'` | Order-level aggregate | `analytics.fact_orders.order_status`, `order_id` | Denominator: **all `order_status` values** | `order_purchase_timestamp` | Only explicit `canceled` status counted as canceled (not `unavailable`) | APPROVED |

## Candidate metrics (not approved)
| Name | Definition | Grain | Notes | Status |
|---|---|---|---|---|
| item_gmv | Sum of item prices (`fact_order_items.price`) for qualifying orders | Item/order | Differs from payment-based GMV; approve before use | DRAFT |

## Notes
- Default commercial/volume reporting in this project uses **all `order_status` values** at purchase-time grain unless a metric specifies delivery/review constraints (delivery and review KPIs). Any deviation must be stated explicitly.
- Geographic/category cuts inherit the metric filter above and must preserve grain (no item-level sum used as order count).
