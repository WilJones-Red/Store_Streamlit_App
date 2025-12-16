"""
Page 3: Customer Comparison Analysis
How do cash customers and credit customers compare?
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_loader import load_enriched_transactions, get_payment_comparison

# Reference: https://docs.streamlit.io/develop/api-reference

st.set_page_config(page_title="Customer Comparison", page_icon="-", layout="wide")

st.title("Customer Comparison Analysis")
st.markdown("### Cash vs Credit Customers: A Comprehensive Comparison")
st.markdown("---")

# Load real data using data_loader
df = load_enriched_transactions().collect()

# SIDEBAR FILTERS
with st.sidebar:
    st.header("Filters")
    
    # Date range
    st.subheader("Date Range")
    min_date = df.select(pl.col("date").min()).item()
    max_date = df.select(pl.col("date").max()).item()
    
    date_range = st.date_input(
        "Select period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Store exclusion
    st.subheader("Store Exclusion")
    stores = df.select(pl.col("STORE_NAME").unique()).to_series().sort().to_list()
    excluded_stores = st.multiselect(
        "Exclude stores",
        options=stores,
        default=[]
    )
    
    # Payment type filter
    st.subheader("Payment Types")
    payment_types = ["CASH", "CREDIT/DEBIT"]
    selected_payments = st.multiselect(
        "Select payment types",
        options=payment_types,
        default=payment_types
    )

# Apply filters (exclusion logic)
filtered_df = df.filter(
    (pl.col("date") >= pl.lit(date_range[0])) &
    (pl.col("date") <= pl.lit(date_range[1])) &
    (~pl.col("STORE_NAME").is_in(excluded_stores)) &
    (
        (pl.col("PAYMENT_TYPE").is_in(["CASH"]) if "CASH" in selected_payments else pl.lit(False)) |
        (pl.col("PAYMENT_TYPE").is_in(["CREDIT", "DEBIT"]) if "CREDIT/DEBIT" in selected_payments else pl.lit(False))
    )
)

# Calculate comparison metrics - create payment type grouping
filtered_df = filtered_df.with_columns(
    pl.when(pl.col("PAYMENT_TYPE") == "CASH")
      .then(pl.lit("CASH"))
      .when(pl.col("PAYMENT_TYPE").is_in(["CREDIT", "DEBIT"]))
      .then(pl.lit("CREDIT/DEBIT"))
      .otherwise(pl.lit("OTHER"))
      .alias("payment_group")
)

payment_comparison = (
    filtered_df
    .filter(pl.col("payment_group").is_in(["CASH", "CREDIT/DEBIT"]))
    .group_by("payment_group")
    .agg([
        pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transaction_count"),
        pl.col("total_sales").sum().alias("total_sales"),
        pl.col("total_sales").mean().alias("avg_transaction"),
        pl.col("UNIT_QUANTITY").sum().alias("total_items"),
        pl.col("UNIT_QUANTITY").mean().alias("avg_items_per_transaction")
    ])
    .sort("payment_group")
)

# Get cash and credit stats
cash_stats = payment_comparison.filter(pl.col("payment_group") == "CASH").to_dicts()
cash_stats = cash_stats[0] if len(cash_stats) > 0 else {}

credit_stats = payment_comparison.filter(pl.col("payment_group") == "CREDIT/DEBIT").to_dicts()
credit_stats = credit_stats[0] if len(credit_stats) > 0 else {}

# KPI SECTION
st.subheader("Key Performance Indicators")

# Create two columns for cash vs credit
kpi_col1, kpi_col2 = st.columns(2)

with kpi_col1:
    st.markdown("### Cash Customers")
    cash_metrics = st.columns(3)
    
    with cash_metrics[0]:
        st.metric(
            "Total Transactions",
            f"{cash_stats.get('transaction_count', 0):,}",
            delta=None
        )
    
    with cash_metrics[1]:
        st.metric(
            "Total Sales",
            f"${cash_stats.get('total_sales', 0):,.2f}",
            delta=None
        )
    
    with cash_metrics[2]:
        st.metric(
            "Avg Transaction",
            f"${cash_stats.get('avg_transaction', 0):.2f}",
            delta=None
        )

with kpi_col2:
    st.markdown("### Credit/Debit Customers")
    credit_metrics = st.columns(3)
    
    with credit_metrics[0]:
        st.metric(
            "Total Transactions",
            f"{credit_stats.get('transaction_count', 0):,}",
            delta=f"{credit_stats.get('transaction_count', 0) - cash_stats.get('transaction_count', 0):+,}" if cash_stats else None
        )
    
    with credit_metrics[1]:
        st.metric(
            "Total Sales",
            f"${credit_stats.get('total_sales', 0):,.2f}",
            delta=f"${credit_stats.get('total_sales', 0) - cash_stats.get('total_sales', 0):+,.2f}" if cash_stats else None
        )
    
    with credit_metrics[2]:
        avg_diff = credit_stats.get('avg_transaction', 0) - cash_stats.get('avg_transaction', 0) if cash_stats else 0
        st.metric(
            "Avg Transaction",
            f"${credit_stats.get('avg_transaction', 0):.2f}",
            delta=f"${avg_diff:+.2f}" if cash_stats else None
        )

st.markdown("---")

# QUESTION 1: Most Purchased Products by Customer Type
st.subheader("Most Purchased Products by Customer Type")

# Calculate top products for each payment type
top_products_by_payment = (
    filtered_df
    .filter(pl.col("payment_group").is_in(["CASH", "CREDIT/DEBIT"]))
    .group_by(["payment_group", "POS_DESCRIPTION"])
    .agg([
        pl.col("TRANSACTION_ITEM_ID").n_unique().alias("purchase_count"),
        pl.col("total_sales").sum().alias("total_sales")
    ])
    .sort(["payment_group", "purchase_count"], descending=[False, True])
)

# Get top 10 for each type
top_cash = top_products_by_payment.filter(pl.col("payment_group") == "CASH").head(10)
top_credit = top_products_by_payment.filter(pl.col("payment_group") == "CREDIT/DEBIT").head(10)

prod_col1, prod_col2 = st.columns(2)

with prod_col1:
    st.markdown("#### Top Products - Cash Customers")
    fig_cash = px.bar(
        top_cash.to_pandas(),
        x="purchase_count",
        y="POS_DESCRIPTION",
        orientation='h',
        color="total_sales",
        color_continuous_scale="Greens",
        labels={"POS_DESCRIPTION": "Product", "purchase_count": "Purchase Count", "total_sales": "Total Sales ($)"},
        title="Most Frequently Purchased (Cash)"
    )
    fig_cash.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_cash, use_container_width=True)

with prod_col2:
    st.markdown("#### Top Products - Credit/Debit Customers")
    fig_credit = px.bar(
        top_credit.to_pandas(),
        x="purchase_count",
        y="POS_DESCRIPTION",
        orientation='h',
        color="total_sales",
        color_continuous_scale="Blues",
        labels={"POS_DESCRIPTION": "Product", "purchase_count": "Purchase Count", "total_sales": "Total Sales ($)"},
        title="Most Frequently Purchased (Credit/Debit)"
    )
    fig_credit.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_credit, use_container_width=True)

st.markdown("---")

# QUESTION 2: Total Purchase Amount Comparison
st.subheader("Total Purchase Amount Comparison")

comp_col1, comp_col2 = st.columns(2)

with comp_col1:
    # Pie chart for sales distribution
    fig_pie = px.pie(
        payment_comparison.to_pandas(),
        values="total_sales",
        names="payment_group",
        title="Sales Distribution by Payment Type",
        color="payment_group",
        color_discrete_map={"CASH": "#2ecc71", "CREDIT/DEBIT": "#3498db"}
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

with comp_col2:
    # Bar chart comparing average transaction amounts
    fig_avg = px.bar(
        payment_comparison.to_pandas(),
        x="payment_group",
        y="avg_transaction",
        color="payment_group",
        text="avg_transaction",
        color_discrete_map={"CASH": "#2ecc71", "CREDIT/DEBIT": "#3498db"},
        labels={"payment_group": "Payment Type", "avg_transaction": "Avg Transaction ($)"},
        title="Average Transaction Amount"
    )
    fig_avg.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
    fig_avg.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_avg, use_container_width=True)

st.markdown("---")

# QUESTION 3: Items Count Comparison
st.subheader("Total Number of Items Comparison")

items_col1, items_col2 = st.columns(2)

with items_col1:
    # Bar chart for total items
    fig_items = px.bar(
        payment_comparison.to_pandas(),
        x="payment_group",
        y="total_items",
        color="payment_group",
        text="total_items",
        color_discrete_map={"CASH": "#2ecc71", "CREDIT/DEBIT": "#3498db"},
        labels={"payment_group": "Payment Type", "total_items": "Total Items Sold"},
        title="Total Items Sold by Payment Type"
    )
    fig_items.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig_items.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_items, use_container_width=True)

with items_col2:
    # Average items per transaction
    fig_avg_items = px.bar(
        payment_comparison.to_pandas(),
        x="payment_group",
        y="avg_items_per_transaction",
        color="payment_group",
        text="avg_items_per_transaction",
        color_discrete_map={"CASH": "#2ecc71", "CREDIT/DEBIT": "#3498db"},
        labels={"payment_group": "Payment Type", "avg_items_per_transaction": "Avg Items/Transaction"},
        title="Average Items per Transaction"
    )
    fig_avg_items.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_avg_items.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_avg_items, use_container_width=True)

st.markdown("---")

# TEMPORAL ANALYSIS
st.subheader("Temporal Trends")

# User input for reference line
max_daily_sales = (
    filtered_df
    .group_by(["date", "payment_group"])
    .agg(pl.col("total_sales").sum())
    .select(pl.col("total_sales").max())
    .item()
)

target_sales = st.number_input(
    "Add daily sales target line",
    min_value=0.0,
    max_value=float(max_daily_sales) if max_daily_sales else 10000.0,
    value=5000.0,
    step=500.0,
    help="Add a horizontal reference line for daily sales target"
)

# Weekly sales by payment type
weekly_sales = (
    filtered_df
    .filter(pl.col("payment_group").is_in(["CASH", "CREDIT/DEBIT"]))
    .group_by(["year", "week", "payment_group"])
    .agg([
        pl.col("total_sales").sum().alias("weekly_sales"),
        pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transaction_count")
    ])
    .sort(["year", "week"])
    .with_columns(
        (pl.col("year").cast(pl.Utf8) + "-W" + pl.col("week").cast(pl.Utf8).str.zfill(2)).alias("week_label")
    )
)

fig_temporal = px.line(
    weekly_sales.to_pandas(),
    x="week_label",
    y="weekly_sales",
    color="payment_group",
    markers=True,
    color_discrete_map={"CASH": "#2ecc71", "CREDIT/DEBIT": "#3498db"},
    labels={"week_label": "Week", "weekly_sales": "Weekly Sales ($)", "payment_group": "Payment Type"},
    title="Weekly Sales Trends by Payment Type"
)

# Add target line (weekly = 7 * daily)
fig_temporal.add_hline(
    y=target_sales * 7,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Target: ${target_sales * 7:,.0f}/week"
)

fig_temporal.update_layout(height=500, hovermode="x unified")
st.plotly_chart(fig_temporal, use_container_width=True)

st.markdown("---")

# DETAILED TABLES
st.subheader("Detailed Analysis Tables")

# TABS for different views
tab1, tab2, tab3 = st.tabs(["Summary Statistics", "Category Breakdown", "Product Details"])

with tab1:
    st.markdown("### Payment Type Summary")
    st.dataframe(
        payment_comparison.to_pandas().style.format({
            "transaction_count": "{:,}",
            "total_sales": "${:,.2f}",
            "avg_transaction": "${:.2f}",
            "total_items": "{:,}",
            "avg_items_per_transaction": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.markdown("### Sales by Category and Payment Type")
    category_breakdown = (
        filtered_df
        .filter(pl.col("payment_group").is_in(["CASH", "CREDIT/DEBIT"]))
        .group_by(["payment_group", "CATEGORY"])
        .agg([
            pl.col("total_sales").sum().alias("total_sales"),
            pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transactions")
        ])
        .sort(["payment_group", "total_sales"], descending=[False, True])
    )
    
    st.dataframe(
        category_breakdown.to_pandas().style.format({
            "total_sales": "${:,.2f}",
            "transactions": "{:,}"
        }),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.markdown("### Top Product Details by Payment Type")
    st.markdown("**Cash Customers - Top 20 Products**")
    top_cash_details = (
        filtered_df
        .filter(pl.col("payment_group") == "CASH")
        .group_by("POS_DESCRIPTION")
        .agg([
            pl.col("total_sales").sum().alias("total_sales"),
            pl.col("UNIT_QUANTITY").sum().alias("units_sold"),
            pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transactions")
        ])
        .sort("total_sales", descending=True)
        .head(20)
    )
    
    st.dataframe(
        top_cash_details.to_pandas().style.format({
            "total_sales": "${:,.2f}",
            "units_sold": "{:,.0f}",
            "transactions": "{:,}"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("**Credit/Debit Customers - Top 20 Products**")
    top_credit_details = (
        filtered_df
        .filter(pl.col("payment_group") == "CREDIT/DEBIT")
        .group_by("POS_DESCRIPTION")
        .agg([
            pl.col("total_sales").sum().alias("total_sales"),
            pl.col("UNIT_QUANTITY").sum().alias("units_sold"),
            pl.col("TRANSACTION_ITEM_ID").n_unique().alias("transactions")
        ])
        .sort("total_sales", descending=True)
        .head(20)
    )
    
    st.dataframe(
        top_credit_details.to_pandas().style.format({
            "total_sales": "${:,.2f}",
            "units_sold": "{:,.0f}",
            "transactions": "{:,}"
        }),
        use_container_width=True,
        hide_index=True
    )

# Download options
st.markdown("---")
col_d1, col_d2 = st.columns(2)

with col_d1:
    csv1 = payment_comparison.to_pandas().to_csv(index=False)
    st.download_button(
        label="Download Summary Statistics",
        data=csv1,
        file_name="payment_comparison_summary.csv",
        mime="text/csv"
    )

with col_d2:
    csv2 = category_breakdown.to_pandas().to_csv(index=False)
    st.download_button(
        label="Download Category Breakdown",
        data=csv2,
        file_name="category_breakdown.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Use the filters in the sidebar to customize your comparison analysis")
