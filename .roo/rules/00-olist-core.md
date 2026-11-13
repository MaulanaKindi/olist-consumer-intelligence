# Olist Consumer Intelligence: Project Rules
- Dataset: Olist Brazilian E-Commerce (about 100k orders, 2016-2018), public and anonymized.
- Grain: orders = 1 row per order; order_items = 1 row per item. Joining orders to order_items duplicates order rows.
- Before writing SQL/Python that touches data, read only what is relevant: docs/olist/01_overview.md, docs/olist/02_schema_relations.md, docs/olist/03_kpi_definitions.md (for any metric), docs/olist/04_pitfalls.md, and docs/olist/profile/<schema>.<table>.md for the tables in use.
- Never guess column names or types. If they are not documented, run DESCRIBE or SELECT ... LIMIT 5 first.
- Every analytical result must state: source tables, order_status filter, and grain.
- Do not read the whole docs/ folder at once.
