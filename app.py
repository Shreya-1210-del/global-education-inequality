import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 0. PAGE CONFIGURATION & STRUCTURE
# ==========================================
st.set_page_config(
    page_title="Global Education Inequality Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 1. OPTIMIZED DATA LOADING ENGINE
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("final_df.csv")
    
    # Force data types explicitly for calculation engines
    if "government_expenditure_on_education_total" in df.columns:
        df["government_expenditure_on_education_total"] = pd.to_numeric(
            df["government_expenditure_on_education_total"], errors="coerce"
        )
    if "literacy_rate_adult_total" in df.columns:
        df["literacy_rate_adult_total"] = pd.to_numeric(
            df["literacy_rate_adult_total"], errors="coerce"
        )
    return df

df = load_data()

# ==========================================
# 2. SIDEBAR NAVIGATION & CONTROL PANEL (Layout Polish)
# ==========================================
st.sidebar.header("🕹️ Dashboard Controls")
st.sidebar.markdown("Use these global filters to update the analytical visualizations on the main canvas.")

st.sidebar.write("---")

# Filter A: Country Selector for Section 4
st.sidebar.subheader("Country Deep-Dive Settings")
all_countries = sorted(df["Country Name"].unique())
selected_country = st.sidebar.selectbox("Select a Country to Analyze", all_countries, index=all_countries.index("India") if "India" in all_countries else 0)

st.sidebar.write("---")

# Filter B: Region Selector for Section 5
st.sidebar.subheader("Regional Comparison Settings")
all_regions = sorted(df["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Select Regions to Compare",
    options=all_regions,
    default=["Sub-Saharan Africa", "South Asia", "Middle East & North Africa"]
)

# ==========================================
# 3. MAIN CANVAS: TITLE & INTRO
# ==========================================
st.title("Measuring the Gap: Global Education Inequality")
st.markdown(
    """
An analysis of literacy, enrollment, and spending across 190+ countries (**2000–2023**).
This interface uncovers regional disparities and economic divides using structural metrics sourced from the World Bank.
"""
)

st.write("---")

# ==========================================
# 4. SECTION 2: POLISHED KPI CARDS
# ==========================================
st.header("📈 Key Performance Indicators")
st.caption("A high-level summary of baseline global educational metrics calculated across the entire timeline dataset.")

avg_literacy = df["literacy_rate_adult_total"].mean()
avg_enrollment = df["school_enrollment_primary_x"].mean()
avg_gpi = df["school_enrollment_primary_and_secondary"].mean()

latest_year_data = df[df["Year"] == df["Year"].max()]
crisis_count = len(latest_year_data[latest_year_data["children_out_of_school_primary"] > 1000000])

# Layout division for KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Global Avg Literacy Rate", value=f"{avg_literacy:.1f}%")
with col2:
    st.metric(label="Global Avg Enrollment", value=f"{avg_enrollment:.1f}%")
with col3:
    st.metric(label="Gender Parity Index (GPI)", value=f"{avg_gpi:.2f}")
with col4:
    st.metric(label="Countries w/ >1M Kids Out-of-School", value=crisis_count)

st.write("---")

# ==========================================
# 5. SECTION 3: WORLD MAP INTERACTIVE EXPLORER
# ==========================================
st.header("🗺️ Spatial Analysis: Global Literacy Map")

latest_year = int(df["Year"].max())
df_map_snapshot = df[df["Year"] == latest_year].copy()

fig_map = px.choropleth(
    df_map_snapshot,
    locations="Country Code",
    color="literacy_rate_adult_total",
    hover_name="Country Name",
    color_continuous_scale="RdYlGn",
    title=f"Global Literacy Rates Spatial Aggregation Summary ({latest_year})",
    labels={"literacy_rate_adult_total": "Literacy Rate (%)"},
)
fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
st.plotly_chart(fig_map, use_container_width=True)
st.caption("Figure 1: Interactive Choropleth map illustrating adult literacy rates for the most recent reporting cycle. Deep green denotes high educational attainment thresholds, while red highlights areas requiring structural intervention.")

st.write("---")

# ==========================================
# 6. SECTION 4: COUNTRY FILTER & TIMELINE EXPLORER
# ==========================================
st.header(f"🔍 Country Deep-Dive: {selected_country}")

df_filtered_country = df[df["Country Name"] == selected_country].copy().sort_values(by="Year")

if df_filtered_country["school_enrollment_primary_x"].notna().sum() > 0:
    fig_country_trend = px.line(
        df_filtered_country,
        x="Year",
        y="school_enrollment_primary_x",
        title=f"Primary School Enrollment Trajectory for {selected_country} (2000-2023)",
        labels={"school_enrollment_primary_x": "Gross Enrollment Ratio (%)", "Year": "Calendar Year"},
        markers=True,
    )
    fig_country_trend.update_layout(margin={"r": 20, "t": 50, "l": 40, "b": 40})
    st.plotly_chart(fig_country_trend, use_container_width=True)
    st.caption(f"Figure 2: Longitudinal primary school gross enrollment ratio trend line for {selected_country}. Fluctuations show systemic educational growth or policy variations over two decades.")
else:
    st.warning(f"No primary enrollment timeline records were reported for {selected_country} in the tracking database.")

st.write("---")

# ==========================================
# 7. SECTION 5: REGION COMPARISON GENDER GAP
# ==========================================
st.header("⚖️ Macroeconomic Disparity: Regional Gender Parity")

if selected_regions:
    # Filter for rows matching any of the chosen regions
    df_regional_gap = df[df["Region"].isin(selected_regions)].copy()
    
    # Isolate records where gender data actually exists
    df_regional_gap = df_regional_gap[df_regional_gap["school_enrollment_primary_and_secondary"].notna()].copy()

    if not df_regional_gap.empty:
        # Find the max year available for these specific regions
        latest_gap_year = int(df_regional_gap["Year"].max())
        
        # Strictly isolate that single year's snapshot
        df_regional_latest = df_regional_gap[df_regional_gap["Year"] == latest_gap_year].copy()

        # Compute the absolute distance from perfect parity (1.0)
        df_regional_latest["gap_distance"] = (1.0 - df_regional_latest["school_enrollment_primary_and_secondary"]).abs()
        
        # Sort and take the top 10 unique countries
        df_top10_regional = df_regional_latest.sort_values(by="gap_distance", ascending=False).head(10)

        if not df_top10_regional.empty:
            fig_regional_gap = px.bar(
                df_top10_regional,
                x="school_enrollment_primary_and_secondary",
                y="Country Name",
                orientation="h",
                color="Country Name",
                title=f"Top 10 Widest Gender Parity Gaps in Selected Regions ({latest_gap_year})",
                labels={"school_enrollment_primary_and_secondary": "Gender Parity Index Value", "Country Name": "Country"},
            )
            fig_regional_gap.add_vline(x=1.0, line_dash="dash", line_color="black", annotation_text="Parity (1.0)")
            fig_regional_gap.update_layout(
                margin={"r": 20, "t": 50, "l": 40, "b": 40}, 
                showlegend=False,
                yaxis={'categoryorder':'total descending'} # Keeps bars sorted beautifully
            )
            st.plotly_chart(fig_regional_gap, use_container_width=True)
            st.caption("Figure 3: Horizontal comparison ranking the worst ten gender parity index spreads across selected geographic subsets. A baseline value of 1.0 indicates perfect gender parity.")
        else:
            st.info("No comparative ranking data available for this selection.")
    else:
        st.info("No gender parity data available for the selected regions.")
else:
    st.warning("Please select at least one geographic region from the dropdown menu in the sidebar panel.")

# ==========================================
# 8. SECTION 6: INCOME GROUP DEEP DIVE CRISIS CHART
# ==========================================
st.header("🚨 Demographic Profile: Out-of-School Absolute Counts")

df_crisis_clean = df[df["children_out_of_school_primary"].notna()].copy()

if not df_crisis_clean.empty:
    latest_crisis_year = int(df_crisis_clean["Year"].max())
    df_crisis_snapshot = df_crisis_clean[df_crisis_clean["Year"] == latest_crisis_year].copy()

    df_crisis_grouped = df_crisis_snapshot.groupby(["Region", "Income Group"])["children_out_of_school_primary"].sum().reset_index()

    fig_crisis = px.bar(
        df_crisis_grouped,
        x="children_out_of_school_primary",
        y="Region",
        color="Income Group",
        orientation="h",
        title=f"Primary Out-of-School Children Distribution by Region & Wealth Tier ({latest_crisis_year})",
        labels={"children_out_of_school_primary": "Total Out-of-School Children", "Region": "Geographic Region", "Income Group": "Income Tier"},
    )
    fig_crisis.update_layout(margin={"r": 20, "t": 50, "l": 40, "b": 40}, legend_title_text="Income Group Tier", barmode="stack")
    st.plotly_chart(fig_crisis, use_container_width=True)
    st.caption(f"Figure 4: Stacked horizontal chart illustrating the absolute number of children outside of active school infrastructure globally during the {latest_crisis_year} cycle. Categorized by continent boundaries and sub-sorted by macroeconomic income metrics.")
else:
    st.info("Out-of-school demographic metrics are completely unpopulated in this dataset framework.")
