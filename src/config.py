"""Project configuration: paths, constants, and settings."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Database
DB_DIR = PROJECT_ROOT / "db"
DUCKDB_PATH = DB_DIR / "olist.duckdb"

# Notebooks
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Source code
SRC_DIR = PROJECT_ROOT / "src"

# Queries
QUERIES_DIR = PROJECT_ROOT / "queries"

# Outputs
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FINDINGS_DIR = OUTPUTS_DIR / "findings"
CHARTS_DIR = OUTPUTS_DIR / "charts"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Documentation
DOCS_DIR = PROJECT_ROOT / "docs"

# Tests
TESTS_DIR = PROJECT_ROOT / "tests"

# Expected Olist source files (CSV names from Kaggle dataset)
SOURCE_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# DuckDB schema names
SCHEMA_RAW = "raw"
SCHEMA_STAGING = "staging"
SCHEMA_ANALYTICS = "analytics"

# Analysis grain definitions
# Grain: one row per declared key combination.
GRAIN_DEFINITIONS = {
    "fact_orders": ["order_id"],
    "fact_order_items": ["order_id", "order_item_id"],
    "dim_customers": ["customer_unique_id"],
    "dim_products": ["product_id"],
    "dim_sellers": ["seller_id"],
    "fact_payments": ["order_id", "payment_sequential"],
    "fact_reviews": ["review_id", "order_id"],
    "fact_delivery": ["order_id"],
}

# Review score range
REVIEW_SCORE_MIN = 1
REVIEW_SCORE_MAX = 5

# Data period
DATA_PERIOD_START = "2016-01-01"
DATA_PERIOD_END = "2018-12-31"

# Random seed for reproducibility
RANDOM_SEED = 42
