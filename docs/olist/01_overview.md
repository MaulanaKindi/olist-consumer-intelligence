# Olist: Dataset Overview
- Public Brazilian e-commerce dataset from Olist: about 100k orders from 2016 to 2018, placed across multiple marketplaces in Brazil.
- Real commercial data, anonymized. Store and partner names in review text were replaced with Game of Thrones house names.
- An order can be analyzed from several dimensions: order status, price, payment, freight and delivery performance, customer location, product attributes, and reviews.
- Business flow: a customer buys from the Olist Store, the seller is notified to fulfill the order, and the product is shipped through logistics partners. Once the customer receives the product, or the estimated delivery date passes, the customer receives a satisfaction survey by email (score and comments).
- The separate Olist Marketing Funnel dataset can be joined but is NOT used in this project unless stated.

## Key data rules
1. An order can contain multiple items.
2. Each item in an order can be fulfilled by a different seller.
3. All text identifying stores and partners was replaced with Game of Thrones house names.

## Analysis ideas from the dataset owner
Review NLP, clustering customers who left no review, sales forecasting, delivery performance, product quality by category, feature engineering.
