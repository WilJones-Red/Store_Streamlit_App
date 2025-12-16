"""
Cstore Data Dashboard - DS 350 Final Challenge
Interactive dashboard for analyzing convenience store sales data
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Cstore Data Dashboard",
    page_icon="-",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page
st.title("Cstore Data Dashboard")
st.markdown("### DS 350 Data Science Programming - Final Coding Challenge")
st.markdown("---")

st.markdown("""
## Assignment Overview

This dashboard addresses the **Data to Dashboard** coding challenge, which requires building an interactive 
application to help convenience store owners make data-driven decisions using Streamlit, Docker, and Polars.

### Assignment Requirements Addressed

This application fulfills all technical requirements by leveraging **Streamlit** as the interactive web framework, **Docker** for containerization and reproducibility, **Polars** for high-performance data processing, **Plotly Express** for creating interactive visualizations, and **Cloud Run (GCP)** for scalable cloud deployment. Each technology was selected to meet the specific demands of the assignment while ensuring professional-grade performance and user experience.

### Dashboard Pages

Each page answers a specific business question from the assignment:

#### 1. **Top Products Analysis**
*Question: "Excluding fuels, what are the top five products with the highest weekly sales?"*
- Displays top 5 non-fuel products by weekly sales with interactive charts
- Includes KPIs, temporal comparisons, and dynamic filters
- Leverages caching for performance

#### 2. **Packaged Beverages**
*Question: "In the packaged beverage category, which brands should I drop if I must drop some from the store?"*
- Analyzes brand performance with sales trends and growth metrics
- Provides data-driven recommendations for underperforming brands
- Includes summary tables and temporal visualizations

#### 3. **Customer Comparison**
*Question: "How do cash customers and credit customers compare?"*
- Compares purchase amounts, item counts, and product preferences
- Shows which products are purchased most by each customer type
- Visualizes differences in shopping behavior

#### 4. **Demographics**
*Question: "Provide detailed customer demographics comparison using Census API"*
- Integrates with U.S. Census API for demographic data
- Compares 10+ demographic variables across store locations
- Displays population, income, age, education, housing, and employment data

### Technical Features

All pages include the assignment-required elements: **Caching** through `@st.cache_data` for optimal performance, **KPIs** using `st.metric()` to display key performance indicators with comparisons, **Summary Tables** presenting clean and formatted data, **Interactive Charts** built with Plotly for temporal comparisons, **Filters** allowing users to select date ranges and exclude specific stores or categories, and **Layouts** utilizing columns, containers, and expanders for intuitive organization.

### Data Details

**Dataset**: Idaho convenience store transaction data  
**Stores**: 167 locations across Idaho  
**Time Period**: September 2022 - August 2024  
**Records**: 895,000+ transactions, 80,000+ unique products  
**Exclusions**: Fuel products filtered using NONSCAN_CATEGORY field

---

### How to Use

1. Select a page from the **sidebar navigation**
2. Apply **filters** to customize your analysis
3. Review **KPIs** at the top of each page
4. Explore **interactive charts** (hover for details)
5. Examine **data tables** for detailed breakdowns

### Running This Application

**With Docker:**
```bash
docker compose up
```
Then navigate to http://localhost:8080

**Repository Structure:**
- `app.py` - Main landing page (this page)
- `pages/` - Individual dashboard pages
- `data_loader.py` - Centralized data loading with caching
- `Dockerfile` - Container configuration
- `docker-compose.yaml` - Docker orchestration
- `requirements.txt` - Python dependencies
""")

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### About This Project")
    st.info("""
    **DS 350 Final Challenge**  
    Data Science Programming
    """)
    st.markdown("---")
    st.markdown("### Data Source")
    st.success("167 Idaho Cstore Locations")
    st.markdown("---")
    st.markdown("### Navigation Help")
    st.markdown("""
    - Use the pages above to view different analyses
    - All pages include interactive filters
    - Hover over charts for details
    - Date ranges can be adjusted on each page
    """)
