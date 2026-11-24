from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import os

# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODULE5 = PROJECT_ROOT / "data" / "processed" / "module5"
MODULE6 = PROJECT_ROOT / "data" / "processed" / "module6"

st.set_page_config(
    page_title="RouteRanker Dashboard",
    page_icon="🚌",
    layout="wide"
)

# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    schedule = pd.read_csv(
        MODULE6 / "module6_simulated_hourly_schedule.csv"
    )

    optimization = pd.read_csv(
        MODULE6 / "module6_optimization_comparison.csv"
    )

    module5_summary = pd.read_csv(
        MODULE5 / "module5_summary.csv"
    )

    city_comparison = pd.read_csv(
        MODULE6 / "module6_city_wise_comparison.csv"
    )

    return schedule, optimization, module5_summary, city_comparison


st.title("🚌 RouteRanker")
st.subheader("AI-Powered Public Transit Route Optimization")
st.write(
    "An interactive dashboard for exploring transit routes, "
    "machine learning results, and simulated schedule optimization."
)

try:
    schedule, optimization, module5_summary, city_comparison = load_data()

except FileNotFoundError as error:
    st.error(f"Required project data file not found: {error}")
    st.info("Check that your Module 5 and Module 6 CSV files exist.")
    st.stop()

# -----------------------------
# 6. City filter
# -----------------------------
if "city" in schedule.columns:
    cities = sorted(schedule["city"].dropna().unique())

    selected_city = st.selectbox(
        "Select City",
        ["All Cities"] + cities
    )

    if selected_city == "All Cities":
        filtered = schedule.copy()
    else:
        filtered = schedule[
            schedule["city"] == selected_city
        ].copy()
else:
    st.error("City column is missing from schedule data.")
    st.stop()
# -----------------------------
# 7. Key performance indicators
# -----------------------------
total_routes = (
    filtered["route_key"].nunique()
    if "route_key" in filtered.columns else 0
)

original_trips = (
    filtered["original_trip_count"].sum()
    if "original_trip_count" in filtered.columns else 0
)

simulated_trips = (
    filtered["simulated_trip_count"].sum()
    if "simulated_trip_count" in filtered.columns else 0
)

additional_trips = simulated_trips - original_trips

col1, col2, col3, col4 = st.columns(4)

col1.metric("Routes", f"{total_routes:,}")
col2.metric("Original Trips", f"{original_trips:,.0f}")
col3.metric("Simulated Trips", f"{simulated_trips:,.0f}")
col4.metric("Additional Trips", f"{additional_trips:,.0f}")

st.divider()

# -----------------------------
# 8. Hourly schedule chart
# -----------------------------
st.header("Hourly Transit Schedule")

if "hour" in filtered.columns:
    hourly = (
        filtered.groupby("hour", as_index=False)
        [["original_trip_count", "simulated_trip_count"]]
        .sum()
    )

    chart_data = hourly.melt(
        id_vars="hour",
        value_vars=[
            "original_trip_count",
            "simulated_trip_count"
        ],
        var_name="Schedule",
        value_name="Trips"
    )

    fig = px.line(
        chart_data,
        x="hour",
        y="Trips",
        color="Schedule",
        markers=True,
        title="Original vs Simulated Hourly Trips"
    )

    st.plotly_chart(fig,width="stretch") 

# -----------------------------
#
# -----------------------------
# 9. City-wise comparison
# -----------------------------
st.header("City-wise Transit Comparison")

if "city" in schedule.columns:

    city_data = schedule.groupby("city")[[
        "original_trip_count",
        "simulated_trip_count"
    ]].sum().reset_index()

    fig = px.bar(
        city_data,
        x="city",
        y=["original_trip_count", "simulated_trip_count"],
        barmode="group",
        title="Original vs Simulated Trips by City"
    )

    st.plotly_chart(fig, width="stretch")


# -----------------------------
# 10. Machine learning results
# -----------------------------


# -----------------------------
# 10. Machine Learning Results
# -----------------------------
st.header("Machine Learning Results")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

clusters_path = os.path.join(
    ROOT,
    "data",
    "processed",
    "module5",
    "module5_route_features_with_clusters.csv"
)

if os.path.exists(clusters_path):
    clusters = pd.read_csv(clusters_path)

    st.success("Module 5 clustering data loaded successfully!")
    st.write("Dataset shape:", clusters.shape)

    # K-Means chart
    if "kmeans_cluster" in clusters.columns:
        st.subheader("K-Means Cluster Distribution")

        kmeans_data = (
            clusters["kmeans_cluster"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        kmeans_data.columns = ["Cluster", "Routes"]

        fig = px.bar(
            kmeans_data,
            x="Cluster",
            y="Routes",
            text="Routes",
            title="K-Means Cluster Distribution"
        )

        st.plotly_chart(fig, width="stretch")

    # DBSCAN chart
    if "dbscan_cluster" in clusters.columns:
        st.subheader("DBSCAN Cluster Distribution")

        dbscan_data = (
            clusters["dbscan_cluster"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        dbscan_data.columns = ["Cluster", "Routes"]

        fig = px.bar(
            dbscan_data,
            x="Cluster",
            y="Routes",
            text="Routes",
            title="DBSCAN Cluster Distribution"
        )

        st.plotly_chart(fig, width="stretch")

else:
    st.error("Module 5 clustering dataset not found!")

    

# -----------------------------
# 11. Optimization comparison
# -----------------------------
st.header("Optimization Summary")

if not optimization.empty:
    st.dataframe(optimization, width="stretch")
else:
    st.info("Optimization comparison data is unavailable.")

# -----------------------------
# 12. Route schedule table
# -----------------------------
st.header("Route Schedule Details")

# Show city-wise schedule counts
st.subheader("City-wise Schedule Records")

city_counts = filtered["city"].value_counts().reset_index()
city_counts.columns = ["City", "Number of Records"]

st.dataframe(city_counts, width="stretch")

# Display schedule records from all cities
st.subheader("Schedule Sample")

if selected_city == "All Cities":
    display_schedule = filtered.groupby(
        "city", group_keys=False
    ).head(20)
else:
    display_schedule = filtered.head(100)

st.dataframe(display_schedule, width="stretch")

# -----------------------------
# 13. Footer
# -----------------------------
st.divider()
st.caption(
    "RouteRanker | AI-Powered Public Transit Route Optimization"
)
