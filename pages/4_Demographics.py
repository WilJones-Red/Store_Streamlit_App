"""
Page 4: Demographics Analysis
Provide store owners with detailed demographic comparison within a specified area around their store
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_loader import load_enriched_transactions

# Reference: https://www.census.gov/data/developers/guidance/api-user-guide.html

st.set_page_config(page_title="Demographics", page_icon="-", layout="wide")

st.title("Customer Demographics Analysis")
st.markdown("### Census Data Comparison for Store Locations")
st.markdown("---")

# Load store data from real data
@st.cache_data
def get_store_locations():
    """Get unique stores with their locations from real data"""
    df = load_enriched_transactions().collect()
    
    # Get unique stores - all stores are in Idaho
    stores = (
        df
        .select(["STORE_ID", "STORE_NAME", "CITY", "STATE"])
        .unique()
        .sort("STORE_NAME")
    )
    
    # Create location mapping - Note: Real lat/lon not in dataset, using Idaho county FIPs
    # Jefferson County (Rigby area): 065, Bonneville County (Idaho Falls area): 019
    # Using Idaho state FIPS: 16
    store_dict = {}
    for row in stores.iter_rows(named=True):
        # Simplified: assign counties based on city name patterns
        # In production, would use geocoding API
        county_fips = "065"  # Default to Jefferson County
        if "FALLS" in row["CITY"].upper() or "IDAHO" in row["CITY"].upper():
            county_fips = "019"  # Bonneville County
        
        store_dict[row["STORE_NAME"]] = {
            "store_id": row["STORE_ID"],
            "city": row["CITY"],
            "state": "16",  # Idaho
            "county": county_fips
        }
    
    return store_dict

STORE_LOCATIONS = get_store_locations()

# Cached Census API call
@st.cache_data(ttl=3600)
def get_census_data(state_fips, county_fips):
    """
    Fetch demographic data from Census API
    Reference: https://api.census.gov/data/2021/acs/acs5/examples.html
    """
    # TODO: Add your Census API key
    # Get one free at: https://api.census.gov/data/key_signup.html
    API_KEY = "6a56a0aeaaeebcc085589f1bba02c8950aa126f4"
    
    # ACS 5-Year Estimates - Detailed demographic variables
    # Reference: https://api.census.gov/data/2021/acs/acs5/variables.html
    variables = {
        "B01001_001E": "Total Population",
        "B01002_001E": "Median Age",
        "B19013_001E": "Median Household Income",
        "B25077_001E": "Median Home Value",
        "B23025_005E": "Unemployed",
        "B15003_022E": "Bachelor's Degree",
        "B15003_023E": "Master's Degree",
        "B02001_002E": "White Alone",
        "B02001_003E": "Black or African American",
        "B03003_003E": "Hispanic or Latino",
        "B11001_002E": "Family Households",
        "B25003_002E": "Owner Occupied Housing",
        "B25003_003E": "Renter Occupied Housing",
        "B08303_001E": "Average Commute Time"
    }
    
    var_string = ",".join(variables.keys())
    
    # Construct API URL for county-level data
    url = f"https://api.census.gov/data/2021/acs/acs5?get=NAME,{var_string}&for=county:{county_fips}&in=state:{state_fips}&key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        headers = data[0]
        values = data[1]
        
        # Create dictionary with variable names
        result = {}
        for i, var_code in enumerate(variables.keys()):
            idx = headers.index(var_code)
            value = values[idx]
            # Handle null values
            result[variables[var_code]] = float(value) if value not in [None, "null", "-666666666"] else 0.0
        
        return result
    except Exception as e:
        st.warning(f"Could not fetch Census data: {e}")
        # Return sample data for demonstration
        return {
            "Total Population": 27000,
            "Median Age": 35.5,
            "Median Household Income": 58000,
            "Median Home Value": 245000,
            "Unemployed": 850,
            "Bachelor's Degree": 3500,
            "Master's Degree": 1200,
            "White Alone": 23500,
            "Black or African American": 150,
            "Hispanic or Latino": 2800,
            "Family Households": 6800,
            "Owner Occupied Housing": 5200,
            "Renter Occupied Housing": 3100,
            "Average Commute Time": 22.5
        }

# SIDEBAR
with st.sidebar:
    st.header("Settings")
    
    st.subheader("Store Selection")
    store_names = sorted(list(STORE_LOCATIONS.keys()))
    selected_store = st.selectbox(
        "Primary store for analysis",
        options=store_names
    )
    
    st.subheader("Comparison Options")
    compare_stores = st.checkbox("Compare with another store", value=False)
    
    if compare_stores:
        other_stores = [s for s in store_names if s != selected_store]
        compare_store = st.selectbox(
            "Select store to compare",
            options=other_stores
        )
    
    st.markdown("---")
    st.info("""
    Note: Census data is provided at the county level.
    
    API Reference: [Census API Documentation](https://www.census.gov/data/developers.html)
    """)

# Load data for selected store(s)
store_data = {}

if compare_stores:
    stores_to_analyze = [selected_store, compare_store]
else:
    stores_to_analyze = [selected_store]

for store in stores_to_analyze:
    location = STORE_LOCATIONS[store]
    store_data[store] = get_census_data(location["state"], location["county"])

# Convert to DataFrame for easier manipulation
demo_rows = []
for store, data in store_data.items():
    for variable, value in data.items():
        demo_rows.append({
            "Store": store,
            "Variable": variable,
            "Value": value
        })

demo_df = pl.DataFrame(demo_rows)

# KPI SECTION
st.subheader("Key Demographic Indicators")

if len(stores_to_analyze) == 1:
    # Single store view
    data = store_data[selected_store]
    
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.metric(
            "Total Population",
            f"{data['Total Population']:,.0f}",
            delta=None
        )
    
    with kpi_cols[1]:
        st.metric(
            "Median Age",
            f"{data['Median Age']:.1f} years",
            delta=None
        )
    
    with kpi_cols[2]:
        st.metric(
            "Median Income",
            f"${data['Median Household Income']:,.0f}",
            delta=None
        )
    
    with kpi_cols[3]:
        st.metric(
            "Median Home Value",
            f"${data['Median Home Value']:,.0f}",
            delta=None
        )
    
else:
    # Comparison view
    st.markdown(f"### {selected_store} vs {compare_store} Comparison")
    
    metrics_row1 = st.columns(4)
    store1_data = store_data[selected_store]
    store2_data = store_data[compare_store]
    
    with metrics_row1[0]:
        st.metric(
            f"Population - {selected_store}",
            f"{store1_data['Total Population']:,.0f}",
            delta=None
        )
        st.metric(
            f"Population - {compare_store}",
            f"{store2_data['Total Population']:,.0f}",
            delta=f"{store2_data['Total Population'] - store1_data['Total Population']:+,.0f}"
        )
    
    with metrics_row1[1]:
        st.metric(
            f"Med. Age - {selected_store}",
            f"{store1_data['Median Age']:.1f}",
            delta=None
        )
        st.metric(
            f"Med. Age - {compare_store}",
            f"{store2_data['Median Age']:.1f}",
            delta=f"{store2_data['Median Age'] - store1_data['Median Age']:+.1f}"
        )
    
    with metrics_row1[2]:
        st.metric(
            f"Med. Income - {selected_store}",
            f"${store1_data['Median Household Income']:,.0f}",
            delta=None
        )
        st.metric(
            f"Med. Income - {compare_store}",
            f"${store2_data['Median Household Income']:,.0f}",
            delta=f"${store2_data['Median Household Income'] - store1_data['Median Household Income']:+,.0f}"
        )
    
    with metrics_row1[3]:
        st.metric(
            f"Med. Home - {selected_store}",
            f"${store1_data['Median Home Value']:,.0f}",
            delta=None
        )
        st.metric(
            f"Med. Home - {compare_store}",
            f"${store2_data['Median Home Value']:,.0f}",
            delta=f"${store2_data['Median Home Value'] - store1_data['Median Home Value']:+,.0f}"
        )

st.markdown("---")

# VISUALIZATION SECTION
st.subheader("Demographic Comparisons")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown("#### Population & Economic Indicators")
    
    # Select variables for comparison
    economic_vars = ["Total Population", "Median Household Income", "Median Home Value", "Unemployed"]
    
    economic_df = demo_df.filter(pl.col("Variable").is_in(economic_vars))
    
    if len(stores_to_analyze) > 1:
        fig1 = px.bar(
            economic_df.to_pandas(),
            x="Variable",
            y="Value",
            color="Store",
            barmode="group",
            labels={"Value": "Count/Dollar Amount", "Variable": "Metric"},
            title="Economic Indicators Comparison"
        )
        fig1.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        fig1 = px.bar(
            economic_df.to_pandas(),
            x="Variable",
            y="Value",
            color="Variable",
            labels={"Value": "Count/Dollar Amount", "Variable": "Metric"},
            title="Economic Indicators"
        )
        fig1.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

with viz_col2:
    st.markdown("#### Education Levels")
    
    education_vars = ["Bachelor's Degree", "Master's Degree"]
    education_df = demo_df.filter(pl.col("Variable").is_in(education_vars))
    
    if len(stores_to_analyze) > 1:
        fig2 = px.bar(
            education_df.to_pandas(),
            x="Variable",
            y="Value",
            color="Store",
            barmode="group",
            labels={"Value": "Population Count", "Variable": "Education Level"},
            title="Educational Attainment"
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        fig2 = px.pie(
            education_df.to_pandas(),
            values="Value",
            names="Variable",
            title="Educational Attainment Distribution"
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# HOUSING AND DEMOGRAPHICS
housing_col1, housing_col2 = st.columns(2)

with housing_col1:
    st.markdown("#### Housing Characteristics")
    
    housing_vars = ["Owner Occupied Housing", "Renter Occupied Housing"]
    housing_df = demo_df.filter(pl.col("Variable").is_in(housing_vars))
    
    if len(stores_to_analyze) > 1:
        fig3 = px.bar(
            housing_df.to_pandas(),
            x="Store",
            y="Value",
            color="Variable",
            barmode="stack",
            labels={"Value": "Housing Units", "Store": "Store Location"},
            title="Housing Tenure Comparison"
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        fig3 = px.pie(
            housing_df.to_pandas(),
            values="Value",
            names="Variable",
            title="Housing Tenure Distribution",
            color_discrete_sequence=["#3498db", "#e74c3c"]
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)

with housing_col2:
    st.markdown("#### Racial Demographics")
    
    race_vars = ["White Alone", "Black or African American", "Hispanic or Latino"]
    race_df = demo_df.filter(pl.col("Variable").is_in(race_vars))
    
    if len(stores_to_analyze) > 1:
        # Create a side-by-side comparison
        fig4 = px.bar(
            race_df.to_pandas(),
            x="Variable",
            y="Value",
            color="Store",
            barmode="group",
            labels={"Value": "Population Count", "Variable": "Race/Ethnicity"},
            title="Racial/Ethnic Composition"
        )
        fig4.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        fig4 = px.pie(
            race_df.to_pandas(),
            values="Value",
            names="Variable",
            title="Racial/Ethnic Composition"
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# RADAR CHART COMPARISON
if len(stores_to_analyze) > 1:
    st.subheader("Multi-Dimensional Comparison")
    
    # Normalize data for radar chart
    # Reference: https://plotly.com/python/radar-chart/
    
    comparison_vars = [
        "Total Population",
        "Median Household Income",
        "Bachelor's Degree",
        "Owner Occupied Housing",
        "Family Households"
    ]
    
    radar_data = []
    for store in stores_to_analyze:
        values = [store_data[store][var] for var in comparison_vars]
        # Normalize to 0-100 scale
        max_vals = [max(store_data[s][var] for s in stores_to_analyze) for var in comparison_vars]
        normalized = [(v / m * 100) if m > 0 else 0 for v, m in zip(values, max_vals)]
        
        radar_data.append({
            "Store": store,
            "Variables": comparison_vars,
            "Values": normalized
        })
    
    fig_radar = go.Figure()
    
    for data in radar_data:
        fig_radar.add_trace(go.Scatterpolar(
            r=data["Values"],
            theta=data["Variables"],
            fill='toself',
            name=data["Store"]
        ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Normalized Demographic Comparison (0-100 scale)",
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# DETAILED TABLES
st.subheader("Detailed Demographic Data")

# TABS
tab1, tab2, tab3 = st.tabs(["Complete Data", "Store Profiles", "Data Sources"])

with tab1:
    st.markdown("### All Demographic Variables")
    
    # Pivot data for better display
    if len(stores_to_analyze) > 1:
        pivot_df = demo_df.pivot(
            index="Variable",
            columns="Store",
            values="Value"
        )
        st.dataframe(
            pivot_df.to_pandas().style.format("{:,.2f}"),
            use_container_width=True
        )
    else:
        single_store_df = demo_df.filter(pl.col("Store") == selected_store)
        st.dataframe(
            single_store_df.select(["Variable", "Value"]).to_pandas().style.format({"Value": "{:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )

with tab2:
    st.markdown("### Store Location Profiles")
    
    for store in stores_to_analyze:
        with st.expander(f"{store} Store Profile", expanded=True):
            data = store_data[store]
            location = STORE_LOCATIONS[store]
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Location Details**")
                st.write(f"Store ID: {location['store_id']}")
                st.write(f"City: {location['city']}")
                st.write(f"State: Idaho")
                st.write(f"County FIPS: {location['county']}")
            
            with col_b:
                st.markdown("**Key Statistics**")
                st.write(f"Population: {data['Total Population']:,.0f}")
                st.write(f"Median Age: {data['Median Age']:.1f}")
                st.write(f"Median Income: ${data['Median Household Income']:,.0f}")

with tab3:
    st.markdown("### Data Sources & References")
    
    st.markdown("""
    #### U.S. Census Bureau
    
    - **Dataset**: American Community Survey (ACS) 5-Year Estimates (2021)
    - **API**: Census Data API
    - **Documentation**: [https://www.census.gov/data/developers.html](https://www.census.gov/data/developers.html)
    - **Variables**: [ACS 5-Year Variables](https://api.census.gov/data/2021/acs/acs5/variables.html)
    
    #### Geographic Level
    - County-level data
    - State FIPS: 16 (Idaho)
    - Counties: Jefferson (065), Bonneville (019)
    
    #### Variables Included (10+ unique)
    1. Total Population
    2. Median Age
    3. Median Household Income
    4. Median Home Value
    5. Unemployment Count
    6. Bachelor's Degree Attainment
    7. Master's Degree Attainment
    8. White Alone Population
    9. Black or African American Population
    10. Hispanic or Latino Population
    11. Family Households
    12. Owner Occupied Housing Units
    13. Renter Occupied Housing Units
    14. Average Commute Time
    
    #### API Setup
    To use live Census data:
    1. Get a free API key at [https://api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html)
    2. Replace `YOUR_CENSUS_API_KEY_HERE` in the code
    3. Restart the application
    """)

# Download option
st.markdown("---")
csv = demo_df.to_pandas().to_csv(index=False)
st.download_button(
    label="Download Demographic Data",
    data=csv,
    file_name="demographic_analysis.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Census data updates annually. Data shown reflects most recent ACS 5-Year estimates.")
