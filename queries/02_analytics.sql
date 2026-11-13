-- Analytics schema: fact and dimension tables for analysis.
-- Grain rules:
--   fact_orders       : one row per order_id (order level)
--   fact_order_items  : one row per (order_id, order_item_id)
--   dim_customers     : one row per customer_unique_id
--   dim_products      : one row per product_id
--   dim_sellers       : one row per seller_id
--   fact_payments     : one row per payment record
--   fact_reviews      : one row per review_id
--   fact_delivery     : one row per order_id

CREATE SCHEMA IF NOT EXISTS analytics;

-- Base order facts: core order attributes + delivery computed at order level.
CREATE OR REPLACE TABLE analytics.fact_orders AS
WITH base AS (
    SELECT
        o.order_id,
        o.customer_id,
        c.customer_unique_id,
        o.order_status,
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        EXTRACT(year FROM o.order_purchase_timestamp) AS order_purchase_year,
        EXTRACT(month FROM o.order_purchase_timestamp) AS order_purchase_month,
        EXTRACT(dow FROM o.order_purchase_timestamp) AS order_purchase_day_of_week,
        (o.order_delivered_customer_date IS NOT NULL) AS is_delivered,
        -- delivery time in days (purchase -> actual delivery)
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL
                 AND o.order_purchase_timestamp IS NOT NULL
            THEN DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)
            ELSE NULL
        END AS delivery_time_days,
        -- estimated vs actual gap (positive = delivered early)
        CASE
            WHEN o.order_estimated_delivery_date IS NOT NULL
                 AND o.order_delivered_customer_date IS NOT NULL
            THEN DATE_DIFF('day', o.order_delivered_customer_date, o.order_estimated_delivery_date)
            ELSE NULL
        END AS delivery_gap_days
    FROM staging.orders o
    LEFT JOIN staging.customers c ON o.customer_id = c.customer_id
    GROUP BY o.order_id, o.customer_id, c.customer_unique_id, o.order_status, o.order_purchase_timestamp,
             o.order_approved_at, o.order_delivered_customer_date,
             o.order_estimated_delivery_date
)
SELECT
    b.order_id,
    b.customer_id,
    b.customer_unique_id,
    b.order_status,
    b.order_purchase_timestamp,
    b.order_approved_at,
    b.order_delivered_customer_date,
    b.order_estimated_delivery_date,
    b.order_purchase_year,
    b.order_purchase_month,
    b.order_purchase_day_of_week,
    b.is_delivered,
    b.delivery_time_days,
    b.delivery_gap_days,
    -- financial: sum of all payments for this order
    COALESCE(
        (SELECT SUM(p.payment_value) FROM staging.payments p
         WHERE p.order_id = b.order_id), 0.0
    ) AS order_total_value,
    -- delivered value: sum of item prices (only if order delivered)
    CASE
        WHEN b.is_delivered
        THEN COALESCE(
            (SELECT SUM(oi.price) FROM staging.order_items oi
             WHERE oi.order_id = b.order_id), 0.0
        )
        ELSE 0.0
    END AS order_delivered_value,
    -- total freight for this order
    COALESCE(
        (SELECT SUM(oi.freight_value) FROM staging.order_items oi
         WHERE oi.order_id = b.order_id), 0.0
    ) AS order_freight_value,
    -- item count at order level
    COALESCE(
        (SELECT COUNT(*) FROM staging.order_items oi
         WHERE oi.order_id = b.order_id), 0
    ) AS order_items_count
FROM base b;

-- fact_order_items: one row per order item, enriched with product + seller attributes.
CREATE OR REPLACE TABLE analytics.fact_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.shipping_limit_date,
    oi.price,
    oi.freight_value,
    p.product_category_name,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    s.seller_city,
    s.seller_state,
    CASE
        WHEN oi.price IS NOT NULL AND oi.price > 0
        THEN oi.freight_value / oi.price
        ELSE NULL
    END AS freight_to_price_ratio
FROM staging.order_items oi
LEFT JOIN staging.products p ON oi.product_id = p.product_id
LEFT JOIN staging.sellers s ON oi.seller_id = s.seller_id;

-- dim_customers: one row per unique customer.
-- Deduplicate by customer_unique_id (take first customer_id per unique_id)
CREATE OR REPLACE TABLE analytics.dim_customers AS
WITH dedup AS (
    SELECT
        customer_unique_id,
        MIN(customer_id) AS customer_id,
        MIN(customer_zip_code_prefix) AS customer_zip_code_prefix,
        MIN(customer_city) AS customer_city,
        MIN(customer_state) AS customer_state
    FROM staging.customers
    GROUP BY customer_unique_id
),
cust_orders AS (
    SELECT
        c.customer_unique_id,
        o.order_id,
        o.order_total_value,
        o.order_purchase_timestamp
    FROM staging.customers c
    JOIN analytics.fact_orders o ON c.customer_id = o.customer_id
)
SELECT
    d.customer_unique_id,
    d.customer_id,
    d.customer_zip_code_prefix,
    d.customer_city,
    d.customer_state,
    COUNT(DISTINCT co.order_id) AS total_orders,
    SUM(co.order_total_value) AS total_spent,
    AVG(co.order_total_value) AS avg_order_value,
    MIN(co.order_purchase_timestamp) AS first_purchase_date,
    MAX(co.order_purchase_timestamp) AS last_purchase_date,
    CASE
        WHEN COUNT(DISTINCT co.order_id) > 1 THEN TRUE
        ELSE FALSE
    END AS is_repeat_customer
FROM dedup d
LEFT JOIN cust_orders co ON d.customer_unique_id = co.customer_unique_id
GROUP BY d.customer_unique_id, d.customer_id, d.customer_zip_code_prefix,
         d.customer_city, d.customer_state;

-- dim_products: one row per product.
CREATE OR REPLACE TABLE analytics.dim_products AS
SELECT
    p.product_id,
    p.product_category_name,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(DISTINCT oi.order_item_id) AS total_items_sold,
    SUM(oi.price) AS total_revenue,
    AVG(oi.price) AS avg_price
FROM staging.products p
LEFT JOIN analytics.fact_order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_category_name, p.product_weight_g,
         p.product_length_cm, p.product_height_cm, p.product_width_cm;

-- dim_sellers: one row per seller.
CREATE OR REPLACE TABLE analytics.dim_sellers AS
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(DISTINCT oi.order_item_id) AS total_items_sold,
    SUM(oi.price) AS total_revenue,
    AVG(oi.price) AS avg_price
FROM staging.sellers s
LEFT JOIN analytics.fact_order_items oi ON s.seller_id = oi.seller_id
GROUP BY s.seller_id, s.seller_city, s.seller_state;

-- fact_payments: one row per payment record.
CREATE OR REPLACE TABLE analytics.fact_payments AS
SELECT
    p.order_id,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value,
    o.order_status,
    CASE
        WHEN p.payment_value IS NOT NULL AND p.payment_installments > 0
        THEN p.payment_value / p.payment_installments
        ELSE NULL
    END AS avg_installment_value,
    o.customer_id
FROM staging.payments p
LEFT JOIN analytics.fact_orders o ON p.order_id = o.order_id;

-- fact_reviews: one row per review.
-- The raw reviews table contains duplicate review_id rows (each linked to
-- different orders in the source). Deduplicate by review_id to preserve grain.
-- Product category is taken from the first order item of that order (to avoid
-- multiplying review rows when an order has multiple items).
CREATE OR REPLACE TABLE analytics.fact_reviews AS
WITH dedup AS (
    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,
        ROW_NUMBER() OVER (PARTITION BY review_id ORDER BY review_creation_date) AS rn
    FROM staging.reviews
),
order_category AS (
    SELECT
        order_id,
        MIN(product_category_name) AS product_category_name
    FROM analytics.fact_order_items
    GROUP BY order_id
)
SELECT
    d.review_id,
    d.order_id,
    d.review_score,
    d.review_comment_title,
    d.review_comment_message,
    d.review_creation_date,
    d.review_answer_timestamp,
    o.customer_id,
    oc.product_category_name,
    CASE
        WHEN d.review_score BETWEEN 1 AND 5 THEN d.review_score
        ELSE NULL
    END AS valid_review_score
FROM dedup d
LEFT JOIN analytics.fact_orders o ON d.order_id = o.order_id
LEFT JOIN order_category oc ON d.order_id = oc.order_id
WHERE d.rn = 1;

-- fact_delivery: one row per order (delivery summary with buckets).
CREATE OR REPLACE TABLE analytics.fact_delivery AS
SELECT
    o.order_id,
    o.delivery_time_days,
    CASE
        WHEN o.delivery_time_days IS NOT NULL
        THEN CASE
            WHEN o.delivery_time_days <= 3 THEN '0-3 days'
            WHEN o.delivery_time_days <= 7 THEN '4-7 days'
            WHEN o.delivery_time_days <= 14 THEN '8-14 days'
            WHEN o.delivery_time_days <= 30 THEN '15-30 days'
            ELSE '30+ days'
        END
        ELSE NULL
    END AS delivery_time_bucket,
    o.delivery_gap_days,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date,
    o.order_freight_value,
    o.order_total_value,
    CASE
        WHEN o.order_total_value IS NOT NULL AND o.order_total_value > 0
        THEN o.order_freight_value / o.order_total_value
        ELSE NULL
    END AS freight_share,
    o.is_delivered,
    o.order_items_count
FROM analytics.fact_orders o;
