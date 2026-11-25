from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="RouteRanker | Transit Intelligence",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. PROJECT PATHS
# This file is expected at: RouteRanker/dashboard/app.py
# ============================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR = PROJECT_DIR / "dashboard" / "outputs"

DATA_FILES = {
    "Processed main dataset": DATA_DIR / "module4_processed_dataset.csv",
    "Clustering features": DATA_DIR / "module5_clustering_features.csv",
    "K-Means assignments": DATA_DIR / "kmeans_route_clusters.csv",
    "DBSCAN assignments": DATA_DIR / "dbscan_cluster_labels.csv",
    "K-Means inference": DATA_DIR / "module6_kmeans_inference.csv",
    "Classification predictions": DATA_DIR / "module6_classification_inference.csv",
    "Route analysis": DATA_DIR / "module6_route_analysis.csv",
    "Hypothetical schedule scenario": DATA_DIR / "module6_hypothetical_schedule_scenario.csv",
    "Before-after comparison": DATA_DIR / "module6_simulation_comparison.csv",
}

OUTPUT_FILES = {
    "KPI summary": OUTPUT_DIR / "dashboard_kpi_summary.csv",
    "City-wise trip analysis": OUTPUT_DIR / "city_wise_trip_analysis.csv",
    "Routes with actual trip reduction": OUTPUT_DIR / "actual_reduced_routes.csv",
}


# ============================================================
# 3. LIGHT, BRIGHT PROFESSIONAL THEME
# ============================================================
st.markdown(
    """
    <style>
    :root {
        --ink: #243653;
        --muted: #657895;
        --blue: #3978e8;
        --purple: #8b5cf6;
        --cyan: #18a8c7;
        --green: #20a879;
        --orange: #f59e0b;
        --pink: #ec6ba8;
        --line: #e4ebf5;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5faff 0%, #f7f5ff 52%, #fff8fc 100%);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,0.72);
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8f5ff 0%, #f0edff 55%, #fff0f7 100%);
        border-right: 1px solid #dce7f5;
    }

    [data-testid="stSidebar"] * {
        color: #344d70;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #315d9b !important;
    }

    .hero {
        background: linear-gradient(110deg, #3989ed 0%, #7779ec 52%, #c27be5 100%);
        padding: 30px 34px;
        border-radius: 22px;
        color: white;
        box-shadow: 0 12px 30px rgba(79, 113, 203, .18);
        margin-bottom: 24px;
    }

    .hero h1 {
        color: white !important;
        font-size: 2.35rem;
        font-weight: 850;
        margin: 0;
    }

    .hero p {
        color: #f4f7ff !important;
        font-size: 1.02rem;
        margin: 8px 0 0 0;
    }

    .hero-chip {
        display: inline-block;
        margin-top: 14px;
        padding: 6px 12px;
        border: 1px solid rgba(255,255,255,.48);
        background: rgba(255,255,255,.16);
        border-radius: 30px;
        color: white;
        font-size: .78rem;
        font-weight: 700;
    }

    h1, h2, h3 {
        color: #315d9b !important;
        font-weight: 800 !important;
    }

    p, li, label, .stMarkdown {
        color: #405574;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e1eaf6;
        border-top: 4px solid #5aa5f5;
        border-radius: 17px;
        padding: 17px 19px;
        box-shadow: 0 6px 18px rgba(67, 101, 155, .08);
        min-height: 112px;
    }

    [data-testid="stMetricLabel"] {
        color: #6a7e9b !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricValue"] {
        color: #294a78 !important;
        font-weight: 850 !important;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 700 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e4ebf5 !important;
        border-radius: 16px !important;
    }

    div[data-baseweb="select"] > div,
    .stTextInput input,
    .stNumberInput input {
        background: #ffffff !important;
        color: #2d4567 !important;
        border-color: #d4e1f2 !important;
        border-radius: 10px !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #dfe8f4;
        border-radius: 13px;
        overflow: hidden;
        background: white;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(100deg, #3989ed, #8b72e9);
        color: white !important;
        border: 0;
        border-radius: 10px;
        font-weight: 750;
        padding: .55rem 1rem;
        box-shadow: 0 5px 13px rgba(75, 116, 210, .16);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(100deg, #2675d8, #795ce0);
        color: white !important;
        border: 0;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    hr {
        border-color: #dfe8f4 !important;
        margin: 1.5rem 0 !important;
    }

    .info-card {
        background: white;
        border: 1px solid #e3eaf5;
        border-left: 5px solid #7b8ff2;
        border-radius: 13px;
        padding: 15px 18px;
        margin: 8px 0 14px 0;
        box-shadow: 0 4px 14px rgba(67, 101, 155, .05);
    }

    .footer {
        text-align: center;
        color: #7a8ba4;
        padding: 22px 8px;
        border-top: 1px solid #e2eaf4;
        margin-top: 30px;
        font-size: .86rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. LOAD FILES SAFELY
# ============================================================
@st.cache_data(show_spinner="Loading RouteRanker datasets...")
def load_csv(path_string):
    return pd.read_csv(path_string, low_memory=False)


datasets = {}
missing_files = []

for label, file_path in {**DATA_FILES, **OUTPUT_FILES}.items():
    if file_path.exists():
        try:
            datasets[label] = load_csv(str(file_path))
        except Exception as exc:
            st.error(f"Could not read {label}: {exc}")
            st.stop()
    else:
        missing_files.append((label, file_path))

if missing_files:
    st.error("Some required project output files are missing.")
    for label, file_path in missing_files:
        st.write(f"**{label}:** `{file_path}`")
    st.info(
        "Check that Modules 1–6 outputs and the three Module 7 CSV files "
        "are present in the existing project folders. This app does not "
        "create replacement sample data."
    )
    st.stop()


# Friendly aliases
main_df = datasets["Processed main dataset"].copy()
features_df = datasets["Clustering features"].copy()
kmeans_df = datasets["K-Means assignments"].copy()
dbscan_df = datasets["DBSCAN assignments"].copy()
kmeans_inference_df = datasets["K-Means inference"].copy()
classification_df = datasets["Classification predictions"].copy()
route_df = datasets["Route analysis"].copy()
simulation_df = datasets["Hypothetical schedule scenario"].copy()
comparison_df = datasets["Before-after comparison"].copy()
kpi_df = datasets["KPI summary"].copy()
city_output_df = datasets["City-wise trip analysis"].copy()
reduced_routes_df = datasets["Routes with actual trip reduction"].copy()

# ============================================================
# 4A. LOAD ROUTE DISPLAY NAMES FROM ORIGINAL GTFS FILES
# ============================================================

def clean_text(value):
    """Return a clean string or an empty string for missing values."""
    if pd.isna(value):
        return ""
    return str(value).strip()


# Build a route-name lookup using the original city-wise GTFS files.
route_name_lookup = {}

RAW_DIR = PROJECT_DIR / "data" / "raw"

# The raw GTFS folder may be absent in a deployment that contains only
# the processed Module 1–6 outputs. In that case, route IDs remain valid labels.
if RAW_DIR.exists():
    city_directories = [path for path in RAW_DIR.iterdir() if path.is_dir()]
else:
    city_directories = []

for city_dir in city_directories:
    routes_file = city_dir / "routes.txt"

    if not routes_file.exists():
        continue

    try:
        raw_routes = pd.read_csv(routes_file, low_memory=False)

        required = {"route_id", "route_short_name", "route_long_name"}
        if not required.issubset(raw_routes.columns):
            continue

        for _, row in raw_routes.iterrows():
            route_id = clean_text(row["route_id"])
            short_name = clean_text(row["route_short_name"])
            long_name = clean_text(row["route_long_name"])

            if short_name:
                display_name = short_name
            elif long_name and long_name != route_id:
                display_name = long_name
            else:
                # The source does not provide a separate route name.
                display_name = route_id

            key = f"{city_dir.name.lower()}||{route_id}"
            route_name_lookup[key] = display_name

    except Exception as exc:
        st.warning(
            f"Could not load GTFS route names for {city_dir.name}: {exc}"
        )


def add_route_display_name(df):
    """Add a readable route label without inventing missing names."""
    result = df.copy()

    if not {"city", "route_id"}.issubset(result.columns):
        return result

    keys = (
        result["city"].astype(str).str.strip().str.lower()
        + "||"
        + result["route_id"].astype(str).str.strip()
    )

    existing_names = (
        result["route_short_name"].map(clean_text)
        if "route_short_name" in result.columns
        else pd.Series("", index=result.index)
    )

    gtfs_names = keys.map(route_name_lookup).fillna("")

    result["route_display_name"] = [
        existing if existing else (gtfs if gtfs else route_id)
        for existing, gtfs, route_id in zip(
            existing_names,
            gtfs_names,
            result["route_id"].astype(str),
        )
    ]

    return result


# Add the display name to all relevant dashboard datasets.
route_df = add_route_display_name(route_df)
classification_df = add_route_display_name(classification_df)
kmeans_df = add_route_display_name(kmeans_df)
dbscan_df = add_route_display_name(dbscan_df)
reduced_routes_df = add_route_display_name(reduced_routes_df)


# ============================================================
# 5. VALIDATION AND HELPER FUNCTIONS
# ============================================================
def require_columns(df, columns, label):
    missing = [column for column in columns if column not in df.columns]
    if missing:
        st.warning(f"{label}: required columns not found: {', '.join(missing)}")
        return False
    return True


def show_table(df, max_height=650):
    """Use a content-based height to avoid large blank table areas."""
    if df is None or df.empty:
        st.info("No records are available for this selection.")
        return
    display_df = df.copy()
    height = min(max(90, 38 * (len(display_df) + 1)), max_height)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=height,
    )


def numeric_series(df, column):
    if column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def route_key(df):
    if not require_columns(df, ["city", "route_id"], "Route key"):
        return pd.Series(index=df.index, dtype="object")
    return df["city"].astype(str).str.strip() + "||" + df["route_id"].astype(str).str.strip()


def gtfs_route_label(value):
    """Decode standard GTFS route_type values used in this project."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return str(value)
    labels = {0: "Tram / Light rail", 1: "Metro / Subway", 2: "Rail", 3: "Bus"}
    return labels.get(number, f"GTFS route type {number}")


def section_note(message):
    st.markdown(f'<div class="info-card">{message}</div>', unsafe_allow_html=True)


# Ensure numerical columns are numeric without changing source files.
for col in [
    "scheduled_trip_count", "stop_count",
    "estimated_straight_line_route_km", "operating_day_count",
    "start_service_hour", "end_service_hour",
]:
    if col in route_df.columns:
        route_df[col] = pd.to_numeric(route_df[col], errors="coerce")

for col in ["Original_Trip_Count", "scheduled_trip_count"]:
    if col in simulation_df.columns:
        simulation_df[col] = pd.to_numeric(simulation_df[col], errors="coerce")

# The KPI CSV is the saved Module 7 output; use its values rather than hardcoding.
if require_columns(kpi_df, ["KPI", "Value"], "KPI summary"):
    kpi_values = dict(zip(kpi_df["KPI"].astype(str), kpi_df["Value"]))
else:
    kpi_values = {}

# Build city-level before/after values from the actual simulation dataset.
if require_columns(
    simulation_df,
    ["city", "Original_Trip_Count", "scheduled_trip_count"],
    "Schedule scenario",
):
    city_trip_summary = (
        simulation_df.groupby("city", as_index=False)
        .agg(
            Original_Scheduled_Trips=("Original_Trip_Count", "sum"),
            Simulated_Scheduled_Trips=("scheduled_trip_count", "sum"),
        )
    )
    city_trip_summary["Trips_Reduced"] = (
        city_trip_summary["Original_Scheduled_Trips"]
        - city_trip_summary["Simulated_Scheduled_Trips"]
    )
    city_trip_summary["Reduction_Percentage"] = (
        city_trip_summary["Trips_Reduced"]
        / city_trip_summary["Original_Scheduled_Trips"].replace(0, np.nan)
        * 100
    ).fillna(0)
else:
    city_trip_summary = pd.DataFrame()


# ============================================================
# 6. SIDEBAR NAVIGATION
# ============================================================
st.sidebar.markdown("## 🚌 RouteRanker")
st.sidebar.caption("Transit intelligence dashboard")
st.sidebar.markdown("---")

pages = [
    "Home / Overview",
    "Dataset Overview",
    "Exploratory Data Analysis",
    "Route Analysis",
    "Clustering Results",
    "Model Predictions",
    "Route Optimization",
    "Metrics Comparison",
    "About Project",
]
page = st.sidebar.radio("NAVIGATION", pages, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Project status**")
st.sidebar.success("Modules 1–6 outputs connected")
st.sidebar.caption("Module 7 · Interactive dashboard")


# ============================================================
# 7. COMMON HEADER
# ============================================================
st.markdown(
    """
    <div class="hero">
        <h1>🚌 RouteRanker</h1>
        <p>AI-Powered Public Transit Route Optimization</p>
        <span class="hero-chip">MODULE 7 · INTERACTIVE DASHBOARD</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PAGE 1 — HOME / OVERVIEW
# ============================================================
if page == "Home / Overview":
    st.header("📊 RouteRanker Overview")
    st.write(
        "Explore the public-transit datasets, route characteristics, "
        "machine-learning outputs and hypothetical schedule scenarios "
        "generated in the previous modules."
    )

    expected_kpis = [
        "Total Routes",
        "Total Cities",
        "Total Scheduled Trips",
        "Average Trips per Route",
        "K-Means Clusters",
        "DBSCAN Clusters (excluding noise)",
        "Actual Routes with Trip Reduction",
        "Total Trips Reduced",
    ]

    if all(key in kpi_values for key in expected_kpis):
        values = [
            ("Total Routes", f"{int(float(kpi_values['Total Routes'])):,}"),
            ("Total Cities", f"{int(float(kpi_values['Total Cities'])):,}"),
            ("Scheduled Trips", f"{int(float(kpi_values['Total Scheduled Trips'])):,}"),
            ("Average Trips / Route", f"{float(kpi_values['Average Trips per Route']):.2f}"),
            ("K-Means Clusters", f"{int(float(kpi_values['K-Means Clusters'])):,}"),
            ("DBSCAN Clusters", f"{int(float(kpi_values['DBSCAN Clusters (excluding noise)'])):,}"),
            ("Reduced Routes", f"{int(float(kpi_values['Actual Routes with Trip Reduction'])):,}"),
            ("Trips Reduced", f"{int(float(kpi_values['Total Trips Reduced'])):,}"),
        ]
        for start in (0, 4):
            cols = st.columns(4)
            for col, (label, value) in zip(cols, values[start:start + 4]):
                col.metric(label, value)
    else:
        st.warning("The KPI summary CSV does not contain all expected KPI names.")

    st.divider()
    left, right = st.columns([1.2, 1])
    with left:

        st.subheader("Routes by City")

        if "city" in route_df.columns:
            city_counts = (
                route_df["city"]
                .astype(str)
                .str.strip()
                .value_counts()
                .sort_values(ascending=False)
            )

            fig, ax = plt.subplots(figsize=(9, 5))

            city_counts.plot(
                kind="bar",
                ax=ax,
                color="#5B9BF5"
            )

            ax.set_ylim(bottom=0)
            ax.set_title("Number of Routes by City")
            ax.set_xlabel("City")
            ax.set_ylabel("Number of Routes")
            ax.tick_params(axis="x", rotation=0)

            for bar in ax.patches:
                height = bar.get_height()
                ax.annotate(
                    f"{int(height):,}",
                    (bar.get_x() + bar.get_width() / 2, height),
                    ha="center",
                    va="bottom"
                )

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.subheader("Route count verification")
            st.dataframe(
                city_counts.rename("Number of Routes").reset_index()
            )

        else:
            st.warning(
                "City column is not available in the route analysis file."
            )

    with right:
        st.subheader("Project workflow")
        st.markdown(
            """
            1. **Module 1:** GTFS data collection
            2. **Module 2:** Feature engineering
            3. **Module 3:** Exploratory data analysis
            4. **Module 4:** Data preprocessing
            5. **Module 5:** Machine learning
            6. **Module 6:** Inference and route optimization
            7. **Module 7:** Interactive dashboard
            """
        )

    section_note(
        "<b>How to interpret the dashboard:</b> scheduled trips are timetable "
        "records, not passenger counts. The schedule changes shown here are "
        "hypothetical simulations, not confirmed real-world service changes."
    )


# ============================================================
# PAGE 2 — DATASET OVERVIEW
# ============================================================
elif page == "Dataset Overview":
    st.header("🗂️ Dataset Overview")
    dataset_names = list(datasets.keys())
    selected_name = st.selectbox("Choose a project dataset", dataset_names)
    selected_df = datasets[selected_name].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", f"{len(selected_df):,}")
    c2.metric("Features", f"{selected_df.shape[1]:,}")
    c3.metric("Missing cells", f"{int(selected_df.isna().sum().sum()):,}")
    c4.metric("Duplicate rows", f"{int(selected_df.duplicated().sum()):,}")

    st.subheader("Dataset preview")
    show_table(selected_df.head(30), max_height=520)

    st.subheader("Column names and data types")
    column_info = pd.DataFrame({
        "Column": selected_df.columns.astype(str),
        "Data type": selected_df.dtypes.astype(str).values,
        "Missing values": selected_df.isna().sum().values,
        "Unique values": selected_df.nunique(dropna=True).values,
    })
    show_table(column_info, max_height=500)

    st.subheader("Statistical summary")
    numeric_df = selected_df.select_dtypes(include=np.number)
    if not numeric_df.empty:
        show_table(numeric_df.describe().T.reset_index(names="Feature").round(3))
    else:
        st.info("This dataset has no numeric columns for statistical summary.")

    st.subheader("Missing-value analysis")
    missing_df = (
        selected_df.isna().sum()
        .rename("Missing values")
        .rename_axis("Column")
        .reset_index()
    )
    missing_df = missing_df[missing_df["Missing values"] > 0]
    if missing_df.empty:
        st.success("No missing values were found in this dataset.")
    else:
        show_table(missing_df)

    st.subheader("Filter records")
    filter_col = st.selectbox(
        "Choose a column",
        ["(No filter)"] + selected_df.columns.astype(str).tolist(),
        key="dataset_filter_column",
    )
    filtered_df = selected_df.copy()
    if filter_col != "(No filter)":
        if selected_df[filter_col].nunique(dropna=True) <= 150:
            options = sorted(
                selected_df[filter_col].dropna().unique().tolist(),
                key=lambda x: str(x),
            )
            selected_values = st.multiselect(
                "Choose value(s)",
                options,
                key="dataset_filter_values",
            )
            if selected_values:
                filtered_df = selected_df[selected_df[filter_col].isin(selected_values)]
        else:
            search_text = st.text_input("Search within this column")
            if search_text:
                filtered_df = selected_df[
                    selected_df[filter_col].astype(str).str.contains(
                        search_text, case=False, na=False
                    )
                ]
    st.caption(f"Showing {len(filtered_df):,} of {len(selected_df):,} records.")
    show_table(filtered_df.head(500), max_height=650)
    st.download_button(
        "⬇️ Download filtered records",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_name.lower().replace(' ', '_')}_filtered.csv",
        mime="text/csv",
    )

    st.subheader("Optional CSV upload")
    uploaded = st.file_uploader("Upload a CSV for temporary inspection", type=["csv"])
    if uploaded is not None:
        try:
            upload_df = pd.read_csv(uploaded)
            st.success(f"Uploaded successfully: {upload_df.shape[0]:,} rows × {upload_df.shape[1]} columns")
            show_table(upload_df.head(30))
        except Exception as exc:
            st.error(f"Could not read the uploaded CSV: {exc}")
        st.caption("Uploaded data is for temporary preview only; it does not replace the project datasets.")


# ============================================================
# PAGE 3 — EXPLORATORY DATA ANALYSIS
# ============================================================
elif page == "Exploratory Data Analysis":
    st.header("📈 Exploratory Data Analysis")

    if "city" in route_df.columns:
        st.subheader("1. Route records by city")
        st.bar_chart(route_df["city"].value_counts(), color="#5B9BF5")

    if require_columns(route_df, ["city", "scheduled_trip_count"], "City trip chart"):
        st.subheader("2. Scheduled trips by city")
        trips_by_city = route_df.groupby("city")["scheduled_trip_count"].sum().sort_values(ascending=False)
        st.bar_chart(trips_by_city, color="#24B99A")

        st.subheader("3. Average scheduled trips per route")
        avg_by_city = route_df.groupby("city")["scheduled_trip_count"].mean().sort_values(ascending=False)
        st.bar_chart(avg_by_city, color="#A78BFA")

    st.subheader("4. Route type distribution")
    route_type_cols = {
        "Metro / Subway": "categorical__route_type_1",
        "Bus": "categorical__route_type_3",
    }
    present = {label: col for label, col in route_type_cols.items() if col in main_df.columns}
    if present:
        counts = pd.Series({label: pd.to_numeric(main_df[col], errors="coerce").fillna(0).sum()
                            for label, col in present.items()})
        st.bar_chart(counts, color="#F59E0B")
    else:
        st.info("The processed main dataset does not contain the expected one-hot route-type columns.")

    numeric_columns = route_df.select_dtypes(include=np.number).columns.tolist()
    if numeric_columns:
        st.subheader("5. Numeric feature distribution")
        feature = st.selectbox("Choose a numeric feature", numeric_columns)
        values = numeric_series(route_df, feature).dropna()
        if not values.empty:
            fig, ax = plt.subplots(figsize=(9, 4))
            sns.histplot(values, kde=True, ax=ax, color="#548CE8")
            ax.set_title(f"Distribution of {feature}")
            ax.set_xlabel(feature)
            ax.set_ylabel("Number of route records")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    st.subheader("6. Correlation heatmap")
    corr_df = route_df.select_dtypes(include=np.number)
    if corr_df.shape[1] >= 2:
        # Avoid an unreadable chart if a source unexpectedly contains many columns.
        corr_df = corr_df.loc[:, corr_df.nunique(dropna=True) > 1]
        if corr_df.shape[1] >= 2:
            fig, ax = plt.subplots(figsize=(11, 7))
            sns.heatmap(corr_df.corr(), cmap="vlag", center=0, annot=True,
                        fmt=".2f", linewidths=.4, ax=ax)
            ax.set_title("Correlation between numeric route features")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Not enough varying numeric features for a correlation heatmap.")
    else:
        st.info("Not enough numeric columns for a correlation heatmap.")

    section_note(
        "The dataset contains route and timetable information. It does not contain "
        "passenger counts, so these charts must not be interpreted as passenger demand "
        "or actual overcrowding."
    )


# ============================================================
# PAGE 4 — ROUTE ANALYSIS
# ============================================================
elif page == "Route Analysis":
    st.header("🛣️ Route Analysis")

    if not require_columns(route_df, ["city", "route_id"], "Route analysis"):
        st.stop()

    # City selection
    cities = sorted(route_df["city"].dropna().astype(str).unique().tolist())
    city_choice = st.selectbox("Select city", ["All cities"] + cities)

    filtered = route_df.copy()

    if city_choice != "All cities":
        filtered = filtered[filtered["city"].astype(str) == city_choice]

    # Search by route name or route ID
    search = st.text_input("Search by route name or route ID")

    if search:
        search_mask = filtered["route_id"].astype(str).str.contains(
            search, case=False, na=False
        )

        if "route_display_name" in filtered.columns:
            search_mask |= filtered["route_display_name"].astype(str).str.contains(
                search, case=False, na=False
            )

        filtered = filtered[search_mask]

    # Route KPIs
    if "scheduled_trip_count" in filtered.columns:
        total_trips = numeric_series(filtered, "scheduled_trip_count").sum()
        average = numeric_series(filtered, "scheduled_trip_count").mean()

        a, b, c = st.columns(3)
        a.metric("Routes in selection", f"{len(filtered):,}")
        b.metric("Scheduled trips", f"{int(total_trips):,}")
        c.metric(
            "Average trips / route",
            f"{average:.2f}" if pd.notna(average) else "N/A"
        )
    else:
        st.metric("Routes in selection", f"{len(filtered):,}")

    # Route records
    st.subheader("Route records")

    display_routes = filtered.copy()

    if "route_display_name" in display_routes.columns:
        display_routes["Route Name"] = display_routes["route_display_name"]

    show_table(display_routes, max_height=650)

    # Compare routes by scheduled trips
    st.subheader("Compare routes by scheduled trips")

    if "scheduled_trip_count" in filtered.columns and not filtered.empty:
        top_n = st.slider("Number of routes to display", 5, 30, 10)

        top = filtered.nlargest(top_n, "scheduled_trip_count").copy()

        if "route_display_name" in top.columns:
            route_labels = top["route_display_name"].astype(str)
        else:
            route_labels = top["route_id"].astype(str)

        top["Route"] = (
            route_labels
            + " (ID: "
            + top["route_id"].astype(str)
            + ")"
        )

        st.bar_chart(
            top.set_index("Route")["scheduled_trip_count"],
            color="#27B99A"
        )
    else:
        st.info("No route records are available for this comparison.")

    # Numeric route statistics
    st.subheader("Numeric route statistics")

    stats = filtered.select_dtypes(include=np.number)

    if not stats.empty:
        show_table(stats.describe().T.reset_index(names="Feature").round(2))
    else:
       st.info("No numeric route characteristics are available.")




# ============================================================
# PAGE 5 — CLUSTERING RESULTS
# ============================================================
elif page == "Clustering Results":
    st.header("🧩 Route Clustering Results")
    algorithm = st.radio("Choose clustering algorithm", ["K-Means", "DBSCAN"], horizontal=True)

    cluster_df = (kmeans_df if algorithm == "K-Means" else dbscan_df).copy()
    if not require_columns(cluster_df, ["city", "route_id", "Cluster"], algorithm):
        st.stop()

    cluster_df["Cluster"] = pd.to_numeric(cluster_df["Cluster"], errors="coerce")
    counts = cluster_df["Cluster"].value_counts().sort_index()
    st.subheader(f"{algorithm} cluster distribution")
    st.bar_chart(counts, color="#8B78E8")

    cluster_options = sorted(cluster_df["Cluster"].dropna().unique().tolist())
    selected_cluster = st.selectbox(
        "Filter by cluster",
        ["All clusters"] + cluster_options,
        format_func=lambda x: "All clusters" if x == "All clusters" else (
            "Noise (-1)" if x == -1 else f"Cluster {int(x)}"
        ),
    )
    chosen = cluster_df.copy()
    if selected_cluster != "All clusters":
        chosen = chosen[chosen["Cluster"] == selected_cluster]

    st.subheader("Routes in selected cluster")
    show_table(chosen, max_height=600)

    st.subheader("Average route characteristics by cluster")
    # Join by city + route_id because route_id values can repeat across cities.
    route_base = route_df.copy()
    route_base["_route_key"] = route_key(route_base)
    chosen_keys = chosen[["city", "route_id", "Cluster"]].copy()
    chosen_keys["_route_key"] = route_key(chosen_keys)
    joined = route_base.merge(
        chosen_keys[["_route_key", "Cluster"]],
        on="_route_key",
        how="inner",
        suffixes=("", "_assignment"),
    )
    # Use only one cluster column; avoid  reset_index inserting a duplicate column.
    if "Cluster_assignment" in joined.columns:
        joined = joined.drop(columns=["Cluster"])
        joined = joined.rename(columns={"Cluster_assignment": "Cluster"})
    elif "Cluster" not in joined.columns:
        joined["Cluster"] = chosen_keys["Cluster"].values[:len(joined)]

    numeric_features = [
        col for col in joined.select_dtypes(include=np.number).columns
        if col != "Cluster"
    ]
    if numeric_features and not joined.empty:
        summary = joined.groupby("Cluster")[numeric_features].mean(numeric_only=True)
        summary_table = summary.copy()
        summary_table.insert(0, "Cluster", summary_table.index)
        show_table(summary_table.reset_index(drop=True), max_height=500)

        selected_feature = st.selectbox(
            "Choose a feature to compare across clusters",
            numeric_features,
            key="cluster_feature_select",
        )
        st.bar_chart(summary[selected_feature], color="#E89B55")
    else:
        st.info("No numeric route characteristics are available for this cluster selection.")

    if algorithm == "DBSCAN":
        noise_count = int((cluster_df["Cluster"] == -1).sum())
        st.info(
            f"DBSCAN identified {noise_count:,} noise records (cluster -1). "
            "Noise means a record was not assigned to a dense cluster; it does not "
            "automatically mean that the route is inefficient."
        )
    section_note(
        "Cluster IDs are labels created by the algorithm. They represent groups "
        "of similar feature patterns and should not be interpreted as route-quality rankings."
    )


# ============================================================
# PAGE 6 — MODEL PREDICTIONS
# ============================================================
elif page == "Model Predictions":
    st.header("🤖 Machine Learning Predictions")
    st.write("These are the saved inference outputs from the previous modules.")

    required = [
        "city", "route_id", "RF_Predicted_Route_Type",
        "XGB_Predicted_Route_Type",
    ]
    if not require_columns(classification_df, required, "Classification predictions"):
        st.stop()

    pred = classification_df.copy()
    pred["_route_key"] = route_key(pred)
    display_cols = ["city", "route_id"]
    if "route_display_name" in pred.columns:
        display_cols.append("route_display_name")
    if "route_short_name" in pred.columns:
        display_cols.append("route_short_name")
    display_cols += [
        col for col in [
            "route_type", "RF_Predicted_Route_Type", "XGB_Predicted_Route_Type"
        ] if col in pred.columns
    ]


    st.subheader("Select a route")

    route_options = pred[display_cols + ["_route_key"]].drop_duplicates(
        "_route_key"
    ).copy()

    # Use route display name when available; otherwise use route ID.
    if "route_display_name" in route_options.columns:
        route_names = route_options["route_display_name"].map(clean_text)
        route_names = route_names.where(
            route_names.ne(""), route_options["route_id"].astype(str)
        )
    elif "route_short_name" in route_options.columns:
        route_names = route_options["route_short_name"].map(clean_text)
        route_names = route_names.where(
            route_names.ne(""), route_options["route_id"].astype(str)
        )
    else:
        route_names = route_options["route_id"].astype(str)

    route_options["_label"] = (
        route_options["city"].astype(str)
        + " | "
        + route_names
        + " | ID: "
        + route_options["route_id"].astype(str)
    )

    route_options = route_options.sort_values("_label")

    labels = route_options["_label"].tolist()

    if labels:
        selected_label = st.selectbox("Choose route", labels)
        selected_key = route_options.loc[
            route_options["_label"] == selected_label, "_route_key"
        ].iloc[0]
        selected_record = pred[pred["_route_key"] == selected_key].head(1)
        st.subheader("Selected route prediction")
        # A one-record dataframe gets a compact height; no artificial empty rows.
        show_table(selected_record[display_cols], max_height=180)

        result = selected_record.iloc[0]
        p1, p2 = st.columns(2)
        p1.metric("Random Forest prediction", gtfs_route_label(result["RF_Predicted_Route_Type"]))
        p2.metric("XGBoost prediction", gtfs_route_label(result["XGB_Predicted_Route_Type"]))
        if "route_type" in result.index:
            st.caption(f"Existing encoded route type: {result['route_type']}")
    else:
        st.warning("No route predictions are available.")

    st.divider()
    st.subheader("Prediction distribution by model")
    model_cols = ["RF_Predicted_Route_Type", "XGB_Predicted_Route_Type"]
    for col in model_cols:
        pred[col] = pd.to_numeric(pred[col], errors="coerce")
    distribution = pd.concat(
        {
            "Random Forest": pred["RF_Predicted_Route_Type"].value_counts(),
            "XGBoost": pred["XGB_Predicted_Route_Type"].value_counts(),
        },
        axis=1,
    ).fillna(0).sort_index()
    distribution.index = [gtfs_route_label(x) for x in distribution.index]
    st.bar_chart(distribution, color=["#4D91E8", "#A27BEA"])
    show_table(distribution.reset_index(names="Predicted route category"))

    section_note(
        "The prediction file contains predicted route-type labels, not probability "
        "scores. Therefore this dashboard compares the saved predictions and does "
        "not invent confidence percentages or retrain the models."
    )



# ============================================================
# PAGE 7 — ROUTE OPTIMIZATION
# ============================================================
elif page == "Route Optimization":
    st.header("⚙️ Route Optimization Analysis")

    st.warning(
        "The schedule adjustment below is a hypothetical simulation from Module 6. "
        "It is not a confirmed real-world service change."
    )

    if not require_columns(
        simulation_df,
        ["Original_Trip_Count", "scheduled_trip_count", "city", "route_id"],
        "Schedule simulation",
    ):
        st.stop()

    # Overall simulation metrics
    original = numeric_series(
        simulation_df, "Original_Trip_Count"
    ).sum()

    simulated = numeric_series(
        simulation_df, "scheduled_trip_count"
    ).sum()

    reduced = original - simulated
    pct = (reduced / original * 100) if original else 0

    a, b, c = st.columns(3)

    a.metric("Original scheduled trips", f"{int(original):,}")
    b.metric("Simulated scheduled trips", f"{int(simulated):,}")
    c.metric(
        "Difference",
        f"{int(reduced):,}",
        delta=f"{pct:.3f}% change",
    )

    # Actual reduced routes
    st.subheader("Routes with a simulated trip-count reduction")

    if not reduced_routes_df.empty:

        cols = [
            col for col in [
                "city",
                "route_display_name",
                "route_id",
                "Original_Trip_Count",
                "scheduled_trip_count",
                "Scenario_Action",
            ]
            if col in reduced_routes_df.columns
        ]

        show_table(
            reduced_routes_df[cols],
            max_height=260,
        )

    else:
        st.info(
            "The saved reduced-routes output contains no records."
        )

    # City-wise trip reduction
    st.subheader("City-wise trip reduction")

    if not city_trip_summary.empty:

        st.bar_chart(
            city_trip_summary.set_index("city")["Trips_Reduced"],
            color="#20B58B",
        )

        show_table(
            city_trip_summary.round(3),
            max_height=350,
        )

    # Scenario action distribution
    st.subheader("Scenario action distribution")

    if "Scenario_Action" in simulation_df.columns:

        action_counts = simulation_df[
            "Scenario_Action"
        ].value_counts()

        st.bar_chart(
            action_counts,
            color="#A27BEA",
        )

    st.divider()

    # Route merging investigation
    st.subheader("Route merging investigation")

    st.info(
        "A validated route-merging recommendation requires stop-level overlap "
        "or route geometry comparison. Those validated overlap results are not "
        "present in the available Module 6 outputs, so this dashboard does not "
        "label routes as merge candidates."
    )

    # Route splitting investigation
    st.subheader("Route splitting investigation")

    st.info(
        "A validated route-splitting recommendation requires segment-level demand, "
        "stop sequence or route-shape evidence. That evidence is not available in "
        "the supplied Module 6 outputs, so no splitting recommendation is fabricated."
    )

    # Trip-frequency adjustment
    st.subheader("Trip-frequency adjustment")

    st.success(
        f"The existing hypothetical scenario changes the total from "
        f"{int(original):,} to {int(simulated):,} scheduled trips "
        f"({int(reduced):,} fewer trips; {pct:.3f}% change)."
    )

    section_note(
        "A reduction in scheduled trips alone does not prove better service. "
        "Passenger demand, stop coverage, service span and operational constraints "
        "must be checked before any real timetable change."
    )



# ============================================================
# PAGE 8 — CURRENT VS SIMULATED METRICS
# ============================================================
elif page == "Metrics Comparison":
    st.header("📊 Current vs Simulated Results")
    st.write("Values below are read from the saved Module 6 before-after comparison.")

    if not require_columns(comparison_df, ["Metric", "Before", "After", "Difference"], "Comparison"):
        st.stop()

    show_table(comparison_df, max_height=350)

    trip_row = comparison_df[comparison_df["Metric"].astype(str).str.casefold() == "scheduled trips"]
    if not trip_row.empty:
        before = pd.to_numeric(trip_row["Before"], errors="coerce").iloc[0]
        after = pd.to_numeric(trip_row["After"], errors="coerce").iloc[0]
        st.subheader("Scheduled trips: before and after")
        st.bar_chart(pd.Series({"Current": before, "Hypothetical scenario": after}), color="#4D91E8")
        delta = after - before
        st.metric("Change in scheduled trips", f"{int(delta):,}")

    st.subheader("Compare all numeric metrics")
    plot_df = comparison_df.copy()
    plot_df["Before"] = pd.to_numeric(plot_df["Before"], errors="coerce")
    plot_df["After"] = pd.to_numeric(plot_df["After"], errors="coerce")
    plot_df["Difference"] = pd.to_numeric(plot_df["Difference"], errors="coerce")
    chart_df = plot_df.set_index("Metric")[["Before", "After"]].dropna(how="all")
    st.bar_chart(chart_df, color=["#4D91E8", "#27B99A"])

    st.subheader("Difference by metric")
    difference_df = plot_df.set_index("Metric")["Difference"].dropna()
    if not difference_df.empty:
        st.bar_chart(difference_df, color="#A27BEA")
    else:
        st.info("The comparison file has no numeric difference values to chart.")

    section_note(
        "Interpret the comparison carefully: the simulation changes scheduled trip "
        "counts only. Route count, route-level stop totals, estimated straight-line "
        "distance and operating-day totals remain as reported in the saved comparison."
    )


# ============================================================
# PAGE 9 — ABOUT PROJECT
# ============================================================
elif page == "About Project":
    st.header("ℹ️ About RouteRanker")
    st.write(
        "RouteRanker is an AI-powered public transit route analysis project. "
        "It combines GTFS data processing, exploratory analysis, machine learning "
        "and a hypothetical schedule scenario in one Streamlit application."
    )

    st.subheader("Project objectives")
    st.markdown(
        """
        - Analyse public transportation GTFS data from five cities.
        - Explore route and scheduled-trip characteristics.
        - Group similar route records using K-Means and DBSCAN.
        - Display Random Forest and XGBoost route-type predictions.
        - Examine the available hypothetical schedule adjustment.
        - Compare current and simulated network-level metrics.
        """
    )

    st.subheader("Technologies")
    tech_cols = st.columns(4)
    for col, tech in zip(tech_cols, ["Python", "Pandas / NumPy", "Scikit-learn / XGBoost", "Streamlit"]):
        col.markdown(
            f"<div class='info-card' style='text-align:center;font-weight:800'>{tech}</div>",
            unsafe_allow_html=True,
        )

    st.subheader("Module workflow")
    workflow = pd.DataFrame({
        "Module": [f"Module {i}" for i in range(1, 8)],
        "Work": [
            "GTFS data collection",
            "Feature engineering",
            "Exploratory data analysis",
            "Data preprocessing",
            "Machine learning",
            "Inference and route optimization",
            "Frontend and interactive dashboard",
        ],
    })
    show_table(workflow, max_height=350)

    st.subheader("Important project limitations")
    st.markdown(
        """
        - Passenger-count and occupancy data are not available.
        - Scheduled trips are timetable records, not actual passenger usage.
        - Straight-line route distance is not road-network distance.
        - DBSCAN noise does not automatically mean a route is inefficient.
        - Cluster IDs are group labels, not quality rankings.
        - Schedule adjustments are hypothetical and require operational validation.
        - Route merging and splitting need stop-level or route-geometry evidence.
        """
    )


# ============================================================
# 10. FOOTER
# ============================================================
st.markdown(
    """
    <div class="footer">
        <b>RouteRanker</b><br>
        AI-Powered Public Transit Route Optimization<br>
        Module 7 · Frontend and Interactive Dashboard Development
    </div>
    """,
    unsafe_allow_html=True,
)
