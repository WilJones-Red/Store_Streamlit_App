"""
Page 1: Top Products Analysis
Excluding fuels, what are the top five products with the highest weekly sales?

Data Source: Cstore transaction data from Assets/DS350_FA25_Jones_Wil/data
References:
- Streamlit Caching: https://docs.streamlit.io/develop/concepts/architecture/caching
- Polars DataFrame: https://pola-rs.github.io/polars/py-polars/html/reference/dataframe/index.html
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_loader import load_enriched_transactions, get_store_list, get_date_range

st.set_page_config(page_title="Top Products", page_icon="-", layout="wide")

st.title("Top Products Analysis")
st.markdown("### Excluding fuels, what are the top five products with the highest weekly sales?")
st.markdown("---")

# Load data with caching
@st.cache_data(ttl=3600)
def load_data():
    """Load and prepare sales data using Polars"""
    # Load enriched transactions
    df = load_enriched_transactions()
    
    # Exclude fuels using NONSCAN_CATEGORY column
    df = df.filter(pl.col("NONSCAN_CATEGORY") != "FUEL")
    
    return df

# Load data
df = load_data()
stores_df = get_store_list()

# LAYOUT: Sidebar filters
# Reference: https://docs.streamlit.io/develop/api-reference/layout
with st.sidebar:
    st.header("Filters")
    
    # Date range filter
    st.subheader("Date Range")
    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Ensure date_range is a tuple with two elements
    if not isinstance(date_range, tuple):
        date_range = (date_range, date_range)
    elif len(date_range) == 1:
        date_range = (date_range[0], date_range[0])
    
    # Store filter
    st.subheader("Store Exclusion")
    store_options = stores_df["STORE_NAME"].to_list()
    excluded_store_names = st.multiselect(
        "Exclude stores",
        options=store_options,
        default=[],  # Exclude none by default
        help="Select stores to EXCLUDE from analysis"
    )
    
    # Get store IDs for excluded stores
    excluded_store_ids = stores_df.filter(
        pl.col("STORE_NAME").is_in(excluded_store_names)
    ).select(pl.col("STORE_ID").cast(pl.Utf8)).to_series().to_list()
    
    # Category filter  
    st.subheader("Category Exclusion")
    categories = df.filter(pl.col("CATEGORY").is_not_null())["CATEGORY"].unique().sort().to_list()
    excluded_categories = st.multiselect(
        "Exclude categories",
        options=categories,
        default=[],  # Exclude none by default
        help="Select categories to EXCLUDE from analysis"
    )

# Apply filters (exclusion logic)
filtered_df = df.filter(
    (pl.col("date") >= date_range[0]) &
    (pl.col("date") <= date_range[1]) &
    (~pl.col("STORE_ID").is_in(excluded_store_ids)) &
    ((~pl.col("CATEGORY").is_in(excluded_categories)) | (pl.col("CATEGORY").is_null()))
)

# Calculate weekly sales and top 5 products
weekly_sales = (
    filtered_df
    .group_by(["year", "week", "POS_DESCRIPTION", "CATEGORY"])
    .agg([
        pl.col("total_sales").sum().alias("weekly_sales"),
        pl.col("UNIT_QUANTITY").sum().alias("units_sold")
    ])
)

# Get top 5 products by total sales across all weeks
top_products = (
    weekly_sales
    .group_by("POS_DESCRIPTION")
    .agg([
        pl.col("weekly_sales").sum().alias("total_sales"),
        pl.col("units_sold").sum().alias("total_units")
    ])
    .sort("total_sales", descending=True)
    .head(5)
)

# CONTAINER: KPIs
# Reference: https://docs.streamlit.io/develop/api-reference/layout/st.columns
st.subheader("Key Performance Indicators")

if len(top_products) > 0:
    kpi_cols = st.columns(5)
    
    for idx, row in enumerate(top_products.iter_rows(named=True)):
        with kpi_cols[idx]:
            st.metric(
                label=f"#{idx + 1}: {row['POS_DESCRIPTION'][:20]}",
                value=f"${row['total_sales']:,.0f}",
                delta=f"{row['total_units']:,.0f} units"
            )
else:
    st.warning("No products found matching the selected filters. Please adjust your filter criteria.")

st.markdown("---")

# LAYOUT: Two-column layout for charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 5 Products by Sales")
    if len(top_products) > 0:
        # Bar chart
        # Reference: https://plotly.com/python/bar-charts/
        fig1 = px.bar(
            top_products.to_pandas(),
            x="POS_DESCRIPTION",
            y="total_sales",
            color="total_sales",
            color_continuous_scale="Blues",
            labels={"POS_DESCRIPTION": "Product", "total_sales": "Total Sales ($)"},
            title="Total Sales by Product"
        )
        fig1.update_layout(showlegend=False, height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data to display")

with col2:
    st.subheader("Top 5 Products by Units Sold")
    if len(top_products) > 0:
        # Horizontal bar chart
        fig2 = px.bar(
            top_products.to_pandas(),
            x="total_units",
            y="POS_DESCRIPTION",
            orientation='h',
            color="total_units",
            color_continuous_scale="Greens",
            labels={"POS_DESCRIPTION": "Product", "total_units": "Units Sold"},
            title="Total Units Sold by Product"
        )
        fig2.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data to display")

st.markdown("---")

# Temporal analysis
st.subheader("Weekly Sales Trends")

# Add user input for reference line
# Reference: https://plotly.com/python/horizontal-vertical-shapes/
if len(top_products) > 0:
    max_weekly = weekly_sales.filter(
        pl.col("POS_DESCRIPTION").is_in(top_products["POS_DESCRIPTION"])
    )["weekly_sales"].max()
    
    threshold = st.number_input(
        "Add sales target line (optional)",
        min_value=0.0,
        max_value=float(max_weekly) if max_weekly else 10000.0,
        value=float(max_weekly * 0.7) if max_weekly else 1000.0,
        step=100.0,
        help="Add a horizontal reference line to the chart"
    )

    # Calculate weekly trends for top products
    weekly_trends = (
        weekly_sales
        .filter(pl.col("POS_DESCRIPTION").is_in(top_products["POS_DESCRIPTION"]))
        .with_columns([
            (pl.col("year").cast(str) + "-W" + pl.col("week").cast(str).str.zfill(2)).alias("week_label")
        ])
        .sort(["year", "week"])
    )

    if len(weekly_trends) > 0:
        # Line chart with reference line
        fig3 = px.line(
            weekly_trends.to_pandas(),
            x="week_label",
            y="weekly_sales",
            color="POS_DESCRIPTION",
            labels={"week_label": "Week", "weekly_sales": "Sales ($)", "POS_DESCRIPTION": "Product"},
            title="Weekly Sales Trends - Top 5 Products"
        )

        # Add horizontal reference line
        fig3.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: ${threshold:,.0f}"
        )

        fig3.update_layout(height=500, hovermode="x unified")
        fig3.update_xaxes(tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Insufficient data for weekly trends")
else:
    st.info("Select filters to view weekly trends")

st.markdown("---")

# GREAT TABLES: Summary table
# Reference: https://posit-dev.github.io/great-tables/
st.subheader("Detailed Summary Table")

# Use expander for the table
# Reference: https://docs.streamlit.io/develop/api-reference/layout/st.expander
with st.expander("View Detailed Product Data", expanded=True):
    if len(top_products) > 0:
        # Reference for Great Tables: https://posit-dev.github.io/great-tables/articles/intro.html
        st.dataframe(
            top_products.to_pandas().style.format({
                "total_sales": "${:,.2f}",
                "total_units": "{:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = top_products.to_pandas().to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"top_products_{date_range[0]}_{date_range[1]}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to display")

# Footer
st.markdown("---")
st.caption("Tip: Use the filters in the sidebar to customize your analysis")
