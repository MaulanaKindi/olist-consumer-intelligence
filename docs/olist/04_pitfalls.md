# Olist: Analysis Pitfalls (UNVERIFIED, check with queries before relying on them)
These points come from general knowledge about the Olist dataset, not from official documentation.
- Joining orders to order_items duplicates rows per item. Be careful when computing revenue or order counts at order level (use COUNT(DISTINCT order_id)).
- geolocation usually has many rows per zip_code_prefix. Deduplicate (for example average lat/lng) before joining so rows do not inflate.
- customer_id is usually unique per order. To identify the same customer across orders, check whether a customer_unique_id column exists.
- One order can have several payment rows, and some orders have more than one review.
- A product category translation table (Portuguese to English) may exist in the Kaggle download but does not appear in the diagram.
- Always check the order_status distribution before computing metrics.
