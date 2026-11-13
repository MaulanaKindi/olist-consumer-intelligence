# Research Design

**Project ID:** OLIST-CI-02  
**Version:** 1.1  
**Status:** Finalized (analysis complete; KPI statuses tracked in `docs/olist/03_kpi_definitions.md`)

## 1. Research Design Overview

This project adopts a quantitative, observational, and exploratory-descriptive research design to examine consumer purchasing behavior and marketplace experience on the Olist e-commerce platform.

The analysis uses historical transactional and operational data observed from 2016-09-04 to 2018-10-17 (`analytics.fact_orders.order_purchase_timestamp`). Multiple datasets are integrated to examine purchasing patterns, customer review scores, delivery performance, freight costs, product-category characteristics, and geographic variations.

The research combines descriptive analytics and diagnostic analysis. Descriptive analysis identifies patterns and distributions; diagnostic analysis explores associations between relevant variables. Statistical measures (e.g. correlations, group comparisons) are applied where appropriate and supported by the data. Findings describe associations within the observed dataset and do not establish causation or represent the entire Brazilian e-commerce market.

The primary unit of analysis varies by research question. Order-level, customer-level, order-item-level, and review-level analyses are conducted where appropriate. Data integration and aggregation must preserve analytical grain to prevent double counting and misleading results.

## 2. Analytical Framework

### 2.1 Consumer Purchase Behavior
Examines order frequency, repeat-purchase behavior, order value, and status mix.  
- **Grain:** customer (`analytics.dim_customers`, key `customer_unique_id`) and order (`analytics.fact_orders`, key `order_id`).  
- **Sources:** `analytics.fact_orders`, `analytics.dim_customers`. **Filter:** all `order_status` values unless stated.

### 2.2 Consumer Experience Intelligence
Examines delivery performance, freight indicators, and customer review scores. Review score is an observable proxy for satisfaction, not a comprehensive experience measure.  
- **Grain:** review/order join at `order_id` (`analytics.fact_reviews` 1/review_id, `analytics.fact_delivery` 1/order).  
- **Sources:** `analytics.fact_reviews`, `analytics.fact_delivery`, `analytics.fact_orders`. **Filter:** `valid_review_score IS NOT NULL`; delivery metrics over delivered/dated orders as applicable.

### 2.3 Product and Category Intelligence
Examines purchasing patterns and review scores across product categories.  
- **Grain:** item (`analytics.fact_order_items`, key `order_id`,`order_item_id`) with review aggregated per `order_id` to avoid fanout.  
- **Sources:** `analytics.fact_order_items`, `analytics.fact_reviews`. **Filter:** all statuses; reviews averaged per order where valid.

### 2.4 Geographic Consumer Intelligence
Examines geographic variation in purchasing and delivery performance by customer state.  
- **Grain:** order joined to customer (`analytics.fact_orders` + `analytics.dim_customers`).  
- **Sources:** `analytics.fact_orders`, `analytics.dim_customers`. **Filter:** all statuses; delivery averages over `is_delivered = TRUE`.

### 2.5 Integrated Intelligence and Decision Support
Domain findings are synthesized into evidence-based implications and recommendations. Each recommendation states the observed finding, business implication, stakeholder, and limitations.

**Process:** data quality assessment → raw/staging/analytics build → grain & transform validation → domain analysis → synthesis → reporting.

## 3. Research Questions and Analytical Mapping

| Domain | Research Question | Analytical Approach | Primary Sources / Variables |
|--------|-------------------|---------------------|-----------------------------|
| Consumer Behavior | What patterns characterize consumer purchasing behavior? | Descriptive distributions, status mix, temporal volume, repeat behavior | `fact_orders` (`order_id`, `order_total_value`, `order_purchase_timestamp`, `order_status`), `dim_customers` (`customer_unique_id`, `is_repeat_customer`) |
| Experience Intelligence | How are delivery performance and freight costs associated with review scores? | Bucketed comparisons, on-time vs late, correlation analysis | `fact_reviews` (`valid_review_score`), `fact_delivery` (`delivery_time_days`, `delivery_gap_days`, `order_freight_value`, `freight_share`) |
| Product Intelligence | How do purchasing patterns and review scores differ across categories? | Category ranking (revenue/orders/items), review comparison with order-level review aggregation | `fact_order_items` (`product_category_name`, `price`), `fact_reviews` (`valid_review_score` by `order_id`) |
| Geographic Intelligence | How do purchasing patterns and delivery performance vary by region? | State-level aggregation and benchmarking | `fact_orders` + `dim_customers` (`customer_state`, `order_total_value`, `delivery_time_days`, `is_delivered`) |

## 4. Unit of Analysis and Analytical Grain

| Grain | Key | Primary Use |
|-------|-----|-------------|
| Customer | `customer_unique_id` (`dim_customers`) | Repeat behavior, customer spend |
| Order | `order_id` (`fact_orders`, `fact_delivery`) | Transaction value, status, delivery performance |
| Item | `order_id`, `order_item_id` (`fact_order_items`) | Category/product revenue and pricing |
| Payment | `order_id`, `payment_sequential` (`fact_payments`) | Payment composition (as needed) |
| Review | `review_id` (`fact_reviews`) | Satisfaction proxy, joined to order |

`analytics.fact_reviews` is deduplicated from raw reviews to preserve 1 row per `review_id`.

## 5. Data Requirements

Mandatory sources (DuckDB `raw`/`staging`/`analytics`): `orders`, `order_items`, `customers`, `products`, `sellers`, `payments`, `reviews`, `geolocation`, `category_translation`. Profiles: `docs/olist/profile/_index.md`.

## 6. Operational Definitions (implemented)

| Metric | Definition | Source / Calculation | Grain |
|--------|------------|----------------------|-------|
| Delivery Time | Days from purchase to customer delivery | `fact_delivery.delivery_time_days` (`DATE_DIFF` purchase→delivered) | Order |
| Delivery Gap | Estimated vs actual delivery (positive = early/on-time relative to estimate) | `fact_delivery.delivery_gap_days` | Order |
| Freight Share | Freight as share of order total | `fact_delivery.freight_share = order_freight_value / order_total_value` | Order |
| Order Total Value | Sum of payments per order | `fact_orders.order_total_value` | Order |
| Repeat Customer | Customer with >1 order | `dim_customers.is_repeat_customer` | Customer |
| Review Score (valid) | Score constrained to 1–5 | `fact_reviews.valid_review_score` | Review |

Candidate business KPIs and approval status remain in `docs/olist/03_kpi_definitions.md`.

## 7. Analytical Methods

1. Descriptive statistics (counts, means, medians, distributions).
2. Exploratory comparisons (time series/monthly volume, buckets, rankings).
3. Diagnostic association analysis (e.g. Spearman correlation, group contrasts).
4. Cross-domain synthesis with explicit grain/filter statements.

## 8. Validation and Quality Controls

- Data quality checks: row counts, null rates, key uniqueness, referential integrity, date and score ranges (`src/validate.py`, `outputs/findings/data_quality.json`).
- Grain integrity: all analytics facts/dims validated (`src/grain_checks.py`, `docs/olist/analytics_validation.json`).
- Transform checks: payment/order totals, item counts, delivery metric consistency (see analytics validation).
- Known notes: raw reviews contain duplicate `review_id` rows (deduplicated in analytics); `product_category_name` has ~1.85% nulls in raw products.

## 9. Intelligence Outputs

- Domain notebooks: `notebooks/00_data_quality.ipynb`–`05_synthesis.ipynb`.
- Findings & charts: `outputs/findings/*`, `outputs/charts/*`.
- Reports: `outputs/reports/executive_intelligence_report.md`, `outputs/reports/strategic_opportunity_matrix.md`.

## 10. Limitations

- Observational secondary data (2016–2018 Olist sample); no causal inference.
- `review_score` is a satisfaction proxy and may be biased by response behavior/timing.
- Repeat-customer measurement depends on `customer_unique_id` linkage within the extract.
- Results may be sensitive to `order_status` filters; operational use requires approved KPI filters.
- Geographic analysis at state level masks within-state heterogeneity.

## 11. References

1. [Olist Dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. [Project Charter](project_charter.md)
3. [System Architecture](system_architecture.md)
4. [Data Dictionary](data_dictionary.md)
5. [Olist Overview](olist/01_overview.md), [Schema Relations](olist/02_schema_relations.md), [KPI Definitions](olist/03_kpi_definitions.md)
