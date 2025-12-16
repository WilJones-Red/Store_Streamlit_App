"""
Page 2: Packaged Beverage Analysis
In the packaged beverage category, which brands should I drop if I must drop some from the store?
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from data_loader import load_enriched_transactions, get_store_list

st.set_page_config(page_title="Packaged Beverages", page_icon="-", layout="wide")

st.title("Packaged Beverage Analysis")
st.markdown("### Which beverage brands should be dropped from inventory?")
st.markdown("---")

# Cached data loading
@st.cache_data(ttl=3600)
def load_beverage_data():
    """Load and prepare beverage sales data"""
    df = load_enriched_transactions()
    
    # Filter to beverages only - use exact category name
    df = df.filter(
        (pl.col("CATEGORY") == "Packaged Beverages") &
        (pl.col("BRAND").is_not_null())
    )
    
    return df

df = load_beverage_data()
stores_df = get_store_list()

# SIDEBAR FILTERS
with st.sidebar:
    st.header("Filters")
    
    # Date range
    st.subheader("Date Range")
    if df.height > 0 and "date" in df.columns:
        min_date = df.select(pl.col("date").min()).collect()[0, 0] if hasattr(df, 'collect') else df["date"].min()
        max_date = df.select(pl.col("date").max()).collect()[0, 0] if hasattr(df, 'collect') else df["date"].max()
    else:
        # Fallback to transaction data if filtered df is empty
        full_df = load_enriched_transactions()
        min_date = full_df["date"].min()
        max_date = full_df["date"].max()
    
    date_range = st.date_input(
        "Select period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Ensure date_range is a tuple with two elements
    if not isinstance(date_range, tuple):
        date_range = (date_range, date_range)
    elif len(date_range) == 1:
        date_range = (date_range[0], date_range[0])
    
    # Store exclusion
    st.subheader("Store Exclusion")
    store_options = stores_df["STORE_NAME"].to_list()
    excluded_store_names = st.multiselect(
        "Exclude stores",
        options=store_options,
        default=[]  # Exclude none by default
    )
    
    excluded_store_ids = stores_df.filter(
        pl.col("STORE_NAME").is_in(excluded_store_names)
    ).select(pl.col("STORE_ID").cast(pl.Utf8)).to_series().to_list()
    
    # Minimum sales threshold
    st.subheader("Performance Thresholds")
    min_sales = st.slider(
        "Minimum total sales ($)",
        min_value=0,
        max_value=10000,
        value=500,
        step=100
    )
    
    min_transactions = st.slider(
        "Minimum transactions",
        min_value=0,
        max_value=1000,
        value=50,
        step=10
    )

# Apply filters (exclusion logic)
filtered_df = df.filter(
    (pl.col("date") >= date_range[0]) &
    (pl.col("date") <= date_range[1]) &
    (~pl.col("STORE_ID").is_in(excluded_store_ids))
)

# Calculate brand performance metrics
brand_performance = (
    filtered_df
    .group_by("BRAND")
    .agg([
        pl.col("total_sales").sum().alias("total_sales"),
        pl.col("UNIT_QUANTITY").sum().alias("total_units"),
        pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transaction_count"),
        pl.col("UNIT_PRICE").mean().alias("avg_price")
    ])
    .with_columns([
        (pl.col("total_sales") / pl.col("transaction_count")).alias("sales_per_transaction")
    ])
    .sort("total_sales", descending=True)
)

# Identify underperforming brands
underperforming = brand_performance.filter(
    (pl.col("total_sales") < min_sales) |
    (pl.col("transaction_count") < min_transactions)
)

# CONTAINER: KPIs
st.subheader("Brand Performance Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Brands",
        len(brand_performance),
        delta=None
    )

with col2:
    st.metric(
        "Underperforming Brands",
        len(underperforming),
        delta=f"-{len(underperforming)} to consider",
        delta_color="inverse"
    )

with col3:
    avg_sales = brand_performance["total_sales"].mean() if len(brand_performance) > 0 else 0
    st.metric(
        "Avg Brand Sales",
        f"${avg_sales:,.0f}"
    )

with col4:
    total_sales = brand_performance["total_sales"].sum() if len(brand_performance) > 0 else 0
    st.metric(
        "Total Beverage Sales",
        f"${total_sales:,.0f}"
    )

st.markdown("---")

# LAYOUT: Two charts side by side
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Sales vs Transaction Count")
    
    if len(brand_performance) > 0:
        fig1 = px.scatter(
            brand_performance.head(30).to_pandas(),
            x="transaction_count",
            y="total_sales",
            size="total_units",
            color="avg_price",
            hover_data=["BRAND", "sales_per_transaction"],
            labels={
                "transaction_count": "Number of Transactions",
                "total_sales": "Total Sales ($)",
                "avg_price": "Avg Price"
            },
            title="Brand Performance Matrix (Top 30)"
        )
        
        # Add threshold lines
        fig1.add_vline(x=min_transactions, line_dash="dash", line_color="red", opacity=0.5)
        fig1.add_hline(y=min_sales, line_dash="dash", line_color="red", opacity=0.5)
        
        fig1.update_layout(height=450)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available")

with chart_col2:
    st.subheader("Top 15 Brands by Sales")
    
    if len(brand_performance) > 0:
        fig2 = px.bar(
            brand_performance.head(15).to_pandas(),
            x="BRAND",
            y="total_sales",
            color="total_sales",
            color_continuous_scale="RdYlGn",
            labels={
                "BRAND": "Brand",
                "total_sales": "Total Sales ($)"
            },
            title="Top Performing Brands"
        )
        fig2.update_layout(height=450, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available")

st.markdown("---")

# TEMPORAL ANALYSIS
st.subheader("Brand Sales Trends Over Time")

benchmark_sales = st.number_input(
    "Add benchmark sales line per week",
    min_value=0.0,
    max_value=1000.0,
    value=100.0,
    step=10.0,
    help="Add a horizontal reference line for target weekly sales"
)

# Get top 10 brands for trend analysis
top_brands = brand_performance.head(10)["BRAND"].to_list()

# Calculate weekly trends
brand_trends = (
    filtered_df
    .filter(pl.col("BRAND").is_in(top_brands))
    .group_by(["year", "week", "BRAND"])
    .agg(pl.col("total_sales").sum().alias("weekly_sales"))
    .with_columns([
        (pl.col("year").cast(str) + "-W" + pl.col("week").cast(str).str.zfill(2)).alias("week_label")
    ])
    .sort(["year", "week"])
)

if len(brand_trends) > 0:
    fig3 = px.line(
        brand_trends.to_pandas(),
        x="week_label",
        y="weekly_sales",
        color="BRAND",
        labels={"week_label": "Week", "weekly_sales": "Sales ($)", "BRAND": "Brand"},
        title="Weekly Sales Trends - Top 10 Brands"
    )
    
    fig3.add_hline(
        y=benchmark_sales,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Benchmark: ${benchmark_sales:,.0f}/week"
    )
    
    fig3.update_layout(height=500, hovermode="x unified")
    fig3.update_xaxes(tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Insufficient data for trend analysis")

st.markdown("---")

# RECOMMENDATIONS SECTION
st.subheader("Drop Recommendations")

tab1, tab2, tab3 = st.tabs(["Underperforming Brands", "All Brands Ranking", "Drop Impact"])

with tab1:
    st.markdown("### Brands Recommended for Removal")
    if len(underperforming) > 0:
        st.warning(f"{len(underperforming)} brand(s) meet removal criteria based on your thresholds")
        
        st.dataframe(
            underperforming.select([
                "BRAND",
                "total_sales",
                "transaction_count",
                "total_units",
                "avg_price"
            ]).to_pandas().style.format({
                "total_sales": "${:,.2f}",
                "transaction_count": "{:,.0f}",
                "total_units": "{:,.0f}",
                "avg_price": "${:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No brands currently meet removal criteria with these thresholds")

with tab2:
    st.markdown("### Complete Brand Performance Ranking")
    st.dataframe(
        brand_performance.select([
            "BRAND",
            "total_sales",
            "total_units",
            "transaction_count",
            "sales_per_transaction"
        ]).to_pandas().style.format({
            "total_sales": "${:,.2f}",
            "total_units": "{:,.0f}",
            "transaction_count": "{:,.0f}",
            "sales_per_transaction": "${:,.2f}"
        }),
        use_container_width=True,
        hide_index=True,
        height=400
    )

with tab3:
    st.markdown("### Impact of Removing Underperforming Brands")
    
    if len(underperforming) > 0:
        lost_sales = underperforming["total_sales"].sum()
        lost_transactions = underperforming["transaction_count"].sum()
        total_brand_sales = brand_performance["total_sales"].sum()
        
        impact_col1, impact_col2, impact_col3 = st.columns(3)
        
        with impact_col1:
            pct_sales = (lost_sales / total_brand_sales * 100) if total_brand_sales > 0 else 0
            st.metric(
                "Lost Sales",
                f"${lost_sales:,.2f}",
                delta=f"-{pct_sales:.1f}% of total",
                delta_color="inverse"
            )
        
        with impact_col2:
            st.metric(
                "Lost Transactions",
                f"{lost_transactions:,.0f}",
                delta_color="inverse"
            )
        
        with impact_col3:
            st.metric(
                "Brands to Remove",
                len(underperforming),
                delta=f"{(len(underperforming)/len(brand_performance)*100):.1f}% of brands"
            )
        
        st.info("Consider: Are the sales lost worth the shelf space gained for better performers?")
    else:
        st.info("No brands recommended for removal with current filter settings")

# Download button
st.markdown("---")
csv = brand_performance.to_pandas().to_csv(index=False)
st.download_button(
    label="Download Full Brand Analysis",
    data=csv,
    file_name=f"beverage_brand_analysis_{date_range[0]}_{date_range[1]}.csv",
    mime="text/csv"
)

st.caption("Adjust thresholds in the sidebar to modify removal criteria")
