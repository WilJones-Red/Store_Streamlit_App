"""
Data Loading Utilities for Cstore Dashboard
Centralized data loading with caching for performance
"""

import polars as pl
import streamlit as st
from pathlib import Path
from datetime import datetime

# Data directory
DATA_DIR = Path("data/data")

@st.cache_data(ttl=3600)
def load_stores():
    """Load store information"""
    return pl.read_parquet(DATA_DIR / "cstore_stores.parquet")

@st.cache_data(ttl=3600)
def load_master_catalog():
    """Load product master catalog with categories"""
    return pl.read_parquet(DATA_DIR / "cstore_master_ctin.parquet")

@st.cache_data(ttl=3600)
def load_payments():
    """Load payment transactions"""
    return pl.read_parquet(DATA_DIR / "cstore_payments.parquet")

@st.cache_data(ttl=3600)
def load_transaction_items():
    """Load all transaction items (lazy scan for performance)"""
    return pl.scan_parquet(str(DATA_DIR / "transaction_items" / "*.parquet"))

@st.cache_resource(ttl=3600)
def load_enriched_transactions():
    """
    Load and enrich transaction items with product categories, payment info, and store details
    Returns a LAZY frame for on-demand processing (Cloud Run optimized)
    """
    # Lazy load for performance
    trans = pl.scan_parquet(str(DATA_DIR / "transaction_items" / "*.parquet"))
    master = pl.scan_parquet(str(DATA_DIR / "cstore_master_ctin.parquet"))
    payments = pl.scan_parquet(str(DATA_DIR / "cstore_payments.parquet"))
    stores = pl.scan_parquet(str(DATA_DIR / "cstore_stores.parquet"))
    
    # Join transactions with product catalog, payments, and stores
    # Note: Cast STORE_ID in stores to string to match transaction data type
    enriched = (
        trans
        .join(master, on="GTIN", how="left")
        .join(
            payments.select(["TRANSACTION_SET_ID", "PAYMENT_TYPE"]),
            on="TRANSACTION_SET_ID",
            how="left"
        )
        .join(
            stores.select(["STORE_ID", "STORE_NAME", "CITY", "STATE"])
                  .with_columns(pl.col("STORE_ID").cast(pl.Utf8)),
            on="STORE_ID",
            how="left"
        )
        .with_columns([
            pl.col("DATE_TIME").cast(pl.Datetime).alias("datetime"),
            pl.col("DATE_TIME").cast(pl.Date).alias("date"),
            (pl.col("UNIT_PRICE") * pl.col("UNIT_QUANTITY")).alias("total_sales"),
            # Extract week info for aggregation
            pl.col("DATE_TIME").cast(pl.Date).dt.week().alias("week"),
            pl.col("DATE_TIME").cast(pl.Date).dt.year().alias("year"),
        ])
    )
    
    # Return lazy frame - only collect when needed by specific queries
    return enriched

@st.cache_data(ttl=3600)
def get_weekly_sales(exclude_fuels=True, stores=None, date_range=None):
    """
    Calculate weekly sales by product
    
    Args:
        exclude_fuels: If True, exclude fuel categories
        stores: List of STORE_IDs to filter (None = all)
        date_range: Tuple of (start_date, end_date) or None
    """
    df = load_enriched_transactions()
    
    # Apply filters
    if exclude_fuels:
        df = df.filter(
            ~pl.col("CATEGORY").str.contains("FUEL|GAS", literal=False) |
            pl.col("CATEGORY").is_null()
        )
    
    if stores:
        df = df.filter(pl.col("STORE_ID").is_in(stores))
    
    if date_range:
        df = df.filter(
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
    
    # Aggregate by week and product
    weekly = (
        df
        .group_by(["year", "week", "POS_DESCRIPTION", "CATEGORY"])
        .agg([
            pl.col("total_sales").sum().alias("weekly_sales"),
            pl.col("UNIT_QUANTITY").sum().alias("units_sold"),
            pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transaction_count")
        ])
    )
    
    return weekly

@st.cache_data(ttl=3600)
def get_payment_comparison(stores=None, date_range=None):
    """
    Compare cash vs credit customer behavior
    Normalizes payment types to CASH vs CREDIT/DEBIT
    """
    df = load_enriched_transactions()
    
    # Normalize payment types
    df = df.with_columns([
        pl.when(pl.col("PAYMENT_TYPE").is_in(["CASH", "CHANGE"]))
        .then(pl.lit("CASH"))
        .when(pl.col("PAYMENT_TYPE").is_in(["CREDIT", "DEBIT"]))
        .then(pl.lit("CREDIT"))
        .otherwise(pl.lit("OTHER"))
        .alias("payment_category")
    ])
    
    # Filter to cash and credit only
    df = df.filter(pl.col("payment_category").is_in(["CASH", "CREDIT"]))
    
    if stores:
        df = df.filter(pl.col("STORE_ID").is_in(stores))
    
    if date_range:
        df = df.filter(
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
    
    return df

@st.cache_data(ttl=3600)
def get_beverage_brands(stores=None, date_range=None):
    """
    Get packaged beverage brand performance
    """
    df = load_enriched_transactions()
    
    # Filter to beverages (packaged)
    df = df.filter(
        pl.col("CATEGORY").str.contains("BEVERAGE|DRINK|SODA|WATER", literal=False)
    )
    
    if stores:
        df = df.filter(pl.col("STORE_ID").is_in(stores))
    
    if date_range:
        df = df.filter(
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
    
    # Aggregate by brand
    brand_perf = (
        df
        .filter(pl.col("BRAND").is_not_null())
        .group_by("BRAND")
        .agg([
            pl.col("total_sales").sum().alias("total_sales"),
            pl.col("UNIT_QUANTITY").sum().alias("units_sold"),
            pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transaction_count"),
            pl.col("UNIT_PRICE").mean().alias("avg_price")
        ])
    )
    
    return brand_perf

def get_store_list():
    """Get list of stores for filtering"""
    stores = load_stores()
    return stores.select(["STORE_ID", "STORE_NAME", "CITY"]).sort("STORE_NAME")

def get_date_range():
    """Get min/max dates from transaction data"""
    trans = load_transaction_items()
    dates = trans.select("DATE_TIME").head(10000).collect()
    return (
        dates["DATE_TIME"].min(),
        dates["DATE_TIME"].max()
    )
