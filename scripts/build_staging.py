"""Build staging schema from raw Olist data."""

import duckdb

DB_PATH = "db/olist.duckdb"
SQL_PATH = "queries/01_staging.sql"


def main():
    conn = duckdb.connect(DB_PATH)
    with open(SQL_PATH, encoding="utf-8") as f:
        sql = f.read()

    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        conn.execute(stmt)

    print("Staging tables built:")
    for t in [
        "orders",
        "order_items",
        "customers",
        "products",
        "sellers",
        "payments",
        "reviews",
        "geolocation",
        "category_translation",
    ]:
        n = conn.execute(f"SELECT count(*) FROM staging.{t}").fetchone()[0]
        print(f"  staging.{t}: {n} rows")

    conn.close()


if __name__ == "__main__":
    main()
