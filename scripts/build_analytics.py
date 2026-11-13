"""Build analytics schema from staging Olist data."""

import duckdb

DB_PATH = "db/olist.duckdb"
SQL_PATH = "queries/02_analytics.sql"


def main():
    conn = duckdb.connect(DB_PATH)
    with open(SQL_PATH, encoding="utf-8") as f:
        sql = f.read()

    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        conn.execute(stmt)

    print("Analytics tables built:")
    for t in [
        "fact_orders",
        "fact_order_items",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "fact_payments",
        "fact_reviews",
        "fact_delivery",
    ]:
        n = conn.execute(f"SELECT count(*) FROM analytics.{t}").fetchone()[0]
        print(f"  analytics.{t}: {n} rows")

    conn.close()


if __name__ == "__main__":
    main()
