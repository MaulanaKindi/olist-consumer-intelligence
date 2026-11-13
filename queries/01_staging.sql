-- Staging schema: cleaned source tables from raw Olist data.
-- Types are cast from VARCHAR to appropriate types where needed.

CREATE SCHEMA IF NOT EXISTS staging;

-- orders: cast timestamps, keep all original columns
CREATE OR REPLACE TABLE staging.orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
    CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
    CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
    CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
FROM raw.orders;

-- order_items: cast numeric fields
CREATE OR REPLACE TABLE staging.order_items AS
SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
    CAST(price AS DOUBLE) AS price,
    CAST(freight_value AS DOUBLE) AS freight_value
FROM raw.order_items;

-- customers: pass through (already clean)
CREATE OR REPLACE TABLE staging.customers AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM raw.customers;

-- products: cast numeric fields
CREATE OR REPLACE TABLE staging.products AS
SELECT
    product_id,
    product_category_name,
    CAST(product_name_lenght AS INTEGER) AS product_name_length,
    CAST(product_description_lenght AS INTEGER) AS product_description_length,
    CAST(product_photos_qty AS INTEGER) AS product_photos_qty,
    CAST(product_weight_g AS INTEGER) AS product_weight_g,
    CAST(product_length_cm AS INTEGER) AS product_length_cm,
    CAST(product_height_cm AS INTEGER) AS product_height_cm,
    CAST(product_width_cm AS INTEGER) AS product_width_cm
FROM raw.products;

-- sellers: pass through
CREATE OR REPLACE TABLE staging.sellers AS
SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM raw.sellers;

-- payments: cast numeric fields
CREATE OR REPLACE TABLE staging.payments AS
SELECT
    order_id,
    CAST(payment_sequential AS INTEGER) AS payment_sequential,
    payment_type,
    CAST(payment_installments AS INTEGER) AS payment_installments,
    CAST(payment_value AS DOUBLE) AS payment_value
FROM raw.payments;

-- reviews: cast score and timestamps
CREATE OR REPLACE TABLE staging.reviews AS
SELECT
    review_id,
    order_id,
    CAST(review_score AS INTEGER) AS review_score,
    review_comment_title,
    review_comment_message,
    CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
    CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
FROM raw.reviews;

-- geolocation: deduplicate by zip_code_prefix (average lat/lng)
CREATE OR REPLACE TABLE staging.geolocation AS
SELECT
    geolocation_zip_code_prefix,
    AVG(CAST(geolocation_lat AS DOUBLE)) AS geolocation_lat,
    AVG(CAST(geolocation_lng AS DOUBLE)) AS geolocation_lng,
    MAX(geolocation_city) AS geolocation_city,  -- arbitrary pick
    MAX(geolocation_state) AS geolocation_state
FROM raw.geolocation
GROUP BY geolocation_zip_code_prefix;

-- category_translation: pass through
CREATE OR REPLACE TABLE staging.category_translation AS
SELECT
    product_category_name,
    product_category_name_english
FROM raw.category_translation;
