import io
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from integrate_gtfs import process_uploaded_gtfs, read_gtfs_zip

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="RouteRanker", page_icon="🚌", layout="wide")

# Theme switching is provided by Streamlit's built-in three-dot menu.


def safe_read(name: str) -> pd.DataFrame:
    path = BASE_DIR / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_resource(ttl=300)
def read_table(name: str) -> pd.DataFrame:
    return safe_read(name)


@st.cache_data(ttl=300)
def load_existing_data():
    return {
        "routes": safe_read("routes.csv"),
        "trips": safe_read("trips.csv"),
        "stop_times": pd.DataFrame(),
        "stops": safe_read("stops.csv"),
        "inventory": safe_read("dataset_inventory.csv"),
        "route_frequency": safe_read("route_trip_frequency.csv"),
        "hourly": safe_read("hourly_route_frequency.csv"),
        "recommendations": safe_read("route_optimization_recommendations.csv"),
        "comparison": safe_read("route_optimization_comparison.csv"),
    }


@st.cache_data(ttl=300)
def build_route_table(route_frequency: pd.DataFrame, hourly: pd.DataFrame, routes: pd.DataFrame):
    route_frequency = route_frequency.copy()
    hourly = hourly.copy()

    if route_frequency.empty:
        return pd.DataFrame()

    if not hourly.empty:
        hourly["scheduled_trips"] = pd.to_numeric(hourly["scheduled_trips"], errors="coerce")
        hourly_summary = hourly.groupby(["city", "route_id"], as_index=False).agg(
            total_scheduled_trips=("scheduled_trips", "sum"),
            peak_hour_trips=("scheduled_trips", "max"),
            avg_hourly_trips=("scheduled_trips", "mean"),
        )
        hourly_summary["peak_hour_ratio"] = np.where(
            hourly_summary["total_scheduled_trips"] > 0,
            hourly_summary["peak_hour_trips"] / hourly_summary["total_scheduled_trips"],
            0,
        )
    else:
        hourly_summary = pd.DataFrame(columns=["city", "route_id", "total_scheduled_trips", "peak_hour_trips", "avg_hourly_trips", "peak_hour_ratio"])

    result = route_frequency.merge(hourly_summary, on=["city", "route_id"], how="left")
    if not routes.empty:
        route_names = routes[[c for c in ["city", "route_id", "route_short_name", "route_long_name", "route_type"] if c in routes.columns]].drop_duplicates(["city", "route_id"])
        result = result.merge(route_names, on=["city", "route_id"], how="left")

    numeric_cols = ["trip_frequency", "total_scheduled_trips", "peak_hour_trips", "avg_hourly_trips", "peak_hour_ratio"]
    for col in numeric_cols:
        if col not in result:
            result[col] = 0

    for col in numeric_cols:
        if col in result:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    for col in numeric_cols:
        if col in result:
            medians = result.groupby("city")[col].transform("median")
            result[col] = result[col].fillna(medians).fillna(0)
    return result


@st.cache_data(ttl=300)
def build_cluster_table(cluster_df: pd.DataFrame, features: tuple[str, ...], cluster_count: int):
    cluster_df = cluster_df.copy()
    scaled = StandardScaler().fit_transform(cluster_df[list(features)])
    cluster_df["KMeans_Cluster"] = KMeans(
        n_clusters=cluster_count, random_state=42, n_init=10
    ).fit_predict(scaled)
    cluster_df["DBSCAN_Cluster"] = DBSCAN(eps=0.8, min_samples=5).fit_predict(scaled)
    return cluster_df


@st.cache_data(ttl=300)
def get_model_predictions(route_table):
    if route_table.empty:
        return pd.DataFrame(), None
    model_path = BASE_DIR / "routeranker_rf_model.pkl"
    scaler_path = BASE_DIR / "routeranker_scaler.pkl"
    if not model_path.exists() or not scaler_path.exists():
        return pd.DataFrame(), "Model artifacts were not found."

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        features = pd.DataFrame({
            "total_scheduled_trips": route_table["total_scheduled_trips"],
            "peak_hour_ratio": route_table["peak_hour_ratio"],
        }).fillna(0)
        scaled = scaler.transform(features)
        predictions = model.predict(scaled)
        probabilities = model.predict_proba(scaled) if hasattr(model, "predict_proba") else None

        result = route_table.copy()
        result["RF_Predicted_Class"] = predictions
        label_map = {0: "Balanced", 1: "Moderate", 2: "Overcrowded"}
        result["RF_Predicted_Category"] = result["RF_Predicted_Class"].map(label_map)
        if probabilities is not None:
            result["RF_Confidence"] = probabilities.max(axis=1)
        return result, None
    except Exception as exc:
        return pd.DataFrame(), f"Could not load or run the trained model: {exc}"


data = load_existing_data()

if "uploaded_gtfs" in st.session_state:
    uploaded = st.session_state["uploaded_gtfs"]
    data["routes"] = uploaded.get("routes", pd.DataFrame())
    data["trips"] = uploaded.get("trips", pd.DataFrame())
    data["stop_times"] = uploaded.get("stop_times", pd.DataFrame())
    data["stops"] = uploaded.get("stops", pd.DataFrame())
    data["route_frequency"] = uploaded.get("route_trip_frequency", pd.DataFrame())
    data["hourly"] = uploaded.get("hourly_route_frequency", pd.DataFrame())

    status_rows = []
    for name in ("routes", "trips", "stop_times", "stops", "calendar"):
        status_rows.append({
            "city": st.session_state.get("uploaded_city", "uploaded-city"),
            "file": name + ".txt",
            "status": "LOADED" if name in uploaded else "MISSING",
            "records": len(uploaded[name]) if name in uploaded else None,
        })
    data["inventory"] = pd.DataFrame(status_rows)


def build_dynamic_recommendations(route_table):
    predictions, error = get_model_predictions(route_table)
    if predictions.empty:
        return pd.DataFrame(), error

    result = predictions.copy()
    median_frequency = result["trip_frequency"].median() if "trip_frequency" in result else 0
    median_peak_ratio = result["peak_hour_ratio"].median() if "peak_hour_ratio" in result else 0
    categories = result["RF_Predicted_Category"]
    overcrowded = categories.eq("Overcrowded")
    result["Advanced_Recommendation"] = np.select(
        [
            overcrowded & result["peak_hour_ratio"].ge(median_peak_ratio),
            overcrowded,
            categories.eq("Moderate"),
            result["trip_frequency"].le(median_frequency),
        ],
        [
            "Increase Frequency / Evaluate Route Splitting",
            "Increase Frequency / Add Extra Trips",
            "Monitor Closely / Minor Schedule Adjustment",
            "Review for Possible Route Merging",
        ],
        default="Maintain Current Schedule",
    )
    return result, None


def clear_dataset_download():
    st.session_state.pop("dataset_download_data", None)
    st.session_state.pop("dataset_download_signature", None)


def build_dynamic_comparison(predictions):
    if predictions.empty:
        return pd.DataFrame()
    counts = predictions["RF_Predicted_Category"].value_counts()
    crowded = int(counts.get("Overcrowded", 0))
    improved = round(crowded * 0.20)
    return pd.DataFrame({
        "Performance": ["Balanced", "Moderate", "Overcrowded"],
        "Before_Optimization": [
            int(counts.get("Balanced", 0)),
            int(counts.get("Moderate", 0)),
            crowded,
        ],
        "After_Optimization": [
            int(counts.get("Balanced", 0)) + improved,
            int(counts.get("Moderate", 0)),
            crowded - improved,
        ],
    })


with st.sidebar:
    st.markdown("## 🚌 RouteRanker")
    st.caption("AI-powered public transit analysis")

    st.markdown("""
    <style>
    .block-container { width: 100%; max-width: 1440px; box-sizing: border-box; padding-top: 3.25rem; padding-bottom: 3rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: 1rem; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 0; }
    [data-testid="stSidebar"] { border-right: 1px solid rgba(127, 127, 127, 0.18); }
    [data-testid="stSidebar"] .stRadio label { font-weight: 600; font-size: 0.86rem; }

    [data-testid="stMetric"] {
        background: rgba(127, 127, 127, 0.06) !important;
        border: 1px solid rgba(127, 127, 127, 0.16) !important;
        border-radius: 14px !important;
        padding: 18px 20px !important;
        box-shadow: 0 7px 22px rgba(15, 23, 42, 0.05) !important;
    }
    [data-testid="stMetricValue"] { font-weight: 700; }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(127, 127, 127, 0.16) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] {
        background: rgba(127, 127, 127, 0.04) !important;
        border: 1px solid rgba(127, 127, 127, 0.16) !important;
        border-radius: 12px !important;
    }
    [data-baseweb="tab-list"] { gap: 8px; }

    .stButton > button, .stDownloadButton > button {
        border-radius: 9px !important;
        font-weight: 700 !important;
        padding: 0.55rem 1rem !important;
    }
    [data-testid="stAlert"] {
        background: rgba(127, 127, 127, 0.06) !important;
        border: 1px solid rgba(127, 127, 127, 0.16) !important;
        border-radius: 12px !important;
    }
    [data-testid="stPlotlyChart"] {
        border: 1px solid rgba(127, 127, 127, 0.16) !important;
        border-radius: 14px !important;
        padding: 8px !important;
        box-shadow: 0 7px 22px rgba(15, 23, 42, 0.05) !important;
    }
    [data-testid="stPlotlyChart"] > div { max-width: 100%; }
    @media (max-width: 900px) {
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            flex: 1 1 260px !important;
            min-width: 0 !important;
        }
    }
    @media (max-width: 640px) {
        .block-container { padding: 3rem 0.75rem 2rem; }
        [data-testid="stHorizontalBlock"] { flex-direction: column !important; align-items: stretch !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        [data-testid="stMetric"] { padding: 12px 14px !important; }
        [data-baseweb="tab-list"] { overflow-x: auto; flex-wrap: nowrap; }
        .stButton > button, .stDownloadButton > button { white-space: normal; }
    }
    </style>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Home / Overview",
            "Dataset Overview",
            "Exploratory Data Analysis",
            "Route Analysis",
            "Clustering Results",
            "Model Predictions",
            "Route Optimization",
            "Metrics Comparison",
            "About / Project Information",
        ],
    )
    st.divider()
    if "uploaded_gtfs" in st.session_state:
        st.success("Using uploaded GTFS data")
        if st.button("Clear uploaded data"):
            st.session_state.pop("uploaded_gtfs", None)
            st.session_state.pop("uploaded_city", None)
            st.rerun()
    else:
        st.caption("Using existing project data")
    st.divider()
    st.caption("Results are based on the available GTFS and generated project outputs.")

if page != "Dataset Overview":
    clear_dataset_download()


if page == "Home / Overview":
    st.title("RouteRanker")
    st.subheader("AI-Powered Public Transit Route Optimization")
    st.write("Explore GTFS data, route patterns, clustering, model predictions, and simulated optimization scenarios from one dashboard.")

    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    inventory = data["inventory"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", route_table["city"].nunique() if not route_table.empty else 0)
    c2.metric("Routes", len(route_table))
    c3.metric("Hourly records", len(data["hourly"]))
    c4.metric("Loaded GTFS tables", int((inventory["status"] == "LOADED").sum()) if not inventory.empty else 0)

    st.info("Predictions and optimization outputs are decision-support results. They are not validated real-world passenger-demand or operational recommendations.")

    if not route_table.empty:
        fig = px.scatter(
            route_table,
            x="trip_frequency",
            y="peak_hour_ratio",
            color="city",
            hover_data=["route_id", "route_long_name"] if "route_long_name" in route_table else ["route_id"],
            title="Route Portfolio: Scheduled Trips vs. Peak-Hour Concentration",
            labels={"trip_frequency": "Scheduled trips", "peak_hour_ratio": "Peak-hour ratio"},
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "Dataset Overview":
    st.title("Dataset Overview")

    source_name = st.selectbox("Dataset to inspect", ["routes", "trips", "stop_times", "stops", "route_trip_frequency", "hourly_route_frequency"], index=4)
    source_map = {
        "routes": data["routes"], "trips": data["trips"], "stop_times": data["stop_times"],
        "stops": data["stops"], "route_trip_frequency": data["route_frequency"],
        "hourly_route_frequency": data["hourly"],
    }
    if source_name == "stop_times" and "uploaded_gtfs" not in st.session_state:
        df = read_table("stop_times.csv")
    else:
        df = source_map[source_name].copy()

    with st.expander("Upload a GTFS ZIP", expanded=False):
        uploaded = st.file_uploader("ZIP containing routes.txt, trips.txt, stop_times.txt, stops.txt, calendar.txt", type="zip")
        city_name = st.text_input("City name", value="uploaded-city")
        if uploaded and st.button("Process uploaded GTFS"):
            try:
                files = read_gtfs_zip(uploaded)
                processed = process_uploaded_gtfs(files, city_name)
                st.session_state["uploaded_gtfs"] = processed
                st.session_state["uploaded_city"] = city_name
                st.success(f"Processed uploaded GTFS: {len(processed)} generated tables")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    uploaded_name = None
    if "uploaded_gtfs" in st.session_state:
        names = list(st.session_state["uploaded_gtfs"])
        uploaded_name = st.selectbox("Uploaded table", names)
        df = st.session_state["uploaded_gtfs"][uploaded_name].copy()

    m1, m2 = st.columns(2)
    m1.metric("Records", f"{len(df):,}")
    m2.metric("Features", df.shape[1])

    with st.form(f"dataset-filter-{source_name}"):
        search = st.text_input("Filter (searches all text columns)")
        st.form_submit_button("Apply filter")
    if search:
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        if len(text_cols):
            mask = pd.Series(False, index=df.index)
            for column in text_cols:
                mask |= df[column].astype("string").str.contains(
                    search, case=False, na=False, regex=False
                )
            df = df.loc[mask]

    dataset_view = st.selectbox(
        "View",
        ["Data Preview", "Schema & Statistics", "Missing Values"],
    )
    if dataset_view == "Data Preview":
        st.dataframe(df.head(100), use_container_width=True)
        if len(df) <= 100_000:
            st.download_button(
                "Download this table",
                df.to_csv(index=False).encode("utf-8"),
                f"{source_name}.csv",
                "text/csv",
            )
        else:
            download_signature = (
                source_name,
                uploaded_name,
                search,
                len(df),
                tuple(df.columns),
            )
            if st.session_state.get("dataset_download_signature") != download_signature:
                st.session_state.pop("dataset_download_data", None)
                st.session_state.pop("dataset_download_signature", None)
            if st.button("Prepare full CSV download"):
                with st.spinner("Preparing the full CSV..."):
                    st.session_state["dataset_download_data"] = df.to_csv(index=False).encode("utf-8")
                    st.session_state["dataset_download_signature"] = download_signature
            if (
                st.session_state.get("dataset_download_signature") == download_signature
                and "dataset_download_data" in st.session_state
            ):
                st.download_button(
                    "Download this table",
                    st.session_state["dataset_download_data"],
                    f"{source_name}.csv",
                    "text/csv",
                    on_click=clear_dataset_download,
                )
    elif dataset_view == "Schema & Statistics":
        stats_df = df.head(100_000)
        if len(df) > len(stats_df):
            st.caption("Statistics use the first 100,000 rows to keep large datasets responsive.")
        schema = pd.DataFrame({"column": stats_df.columns, "dtype": stats_df.dtypes.astype(str).values, "unique": [stats_df[c].nunique(dropna=True) for c in stats_df.columns]})
        st.dataframe(schema, use_container_width=True)
        st.dataframe(stats_df.describe(include="all").transpose(), use_container_width=True)
    else:
        missing = df.isna().sum().reset_index()
        missing.columns = ["column", "missing_values"]
        st.dataframe(missing[missing["missing_values"] > 0], use_container_width=True)

elif page == "Exploratory Data Analysis":
    st.title("Exploratory Data Analysis")
    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])

    if route_table.empty:
        st.warning("No route frequency data is available.")
    else:
        city_options = ["All"] + sorted(route_table["city"].dropna().astype(str).unique().tolist())
        city = st.selectbox("City", city_options)
        filtered = route_table if city == "All" else route_table[route_table["city"] == city]

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(filtered, x="trip_frequency", nbins=30, title="Distribution of Trip Frequency")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.histogram(filtered, x="peak_hour_ratio", nbins=30, title="Distribution of Peak-Hour Ratio")
            st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            top = filtered.nlargest(15, "trip_frequency")
            fig = px.bar(top, x="trip_frequency", y="route_id", orientation="h", title="Top 15 Routes by Scheduled Trips")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if not data["hourly"].empty:
                hourly = data["hourly"].copy()
                if city != "All":
                    hourly = hourly[hourly["city"] == city]
                hourly_profile = hourly.groupby("hour_of_day", as_index=False)["scheduled_trips"].sum()
                fig = px.line(hourly_profile, x="hour_of_day", y="scheduled_trips", markers=True, title="Scheduled Trips by Hour")
                st.plotly_chart(fig, use_container_width=True)

        numeric = filtered.select_dtypes(include=np.number)
        if numeric.shape[1] >= 2:
            fig = px.imshow(numeric.corr(), text_auto=".2f", color_continuous_scale="RdBu", title="Feature Correlation")
            st.plotly_chart(fig, use_container_width=True)

elif page == "Route Analysis":
    st.title("Route Analysis")
    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    if route_table.empty:
        st.warning("No route analysis data is available.")
    else:
        cities = sorted(route_table["city"].dropna().astype(str).unique())
        city = st.selectbox("City", ["All"] + cities)
        filtered = route_table if city == "All" else route_table[route_table["city"] == city]

        route_ids = sorted(filtered["route_id"].dropna().astype(str).unique())
        selected = st.selectbox("Select route", route_ids)
        details = filtered[filtered["route_id"].astype(str) == selected]
        if not details.empty:
            st.dataframe(details, use_container_width=True)

        sort_col = st.selectbox("Compare routes by", [c for c in ["trip_frequency", "total_scheduled_trips", "peak_hour_trips", "peak_hour_ratio"] if c in filtered])
        top = filtered.nlargest(20, sort_col)
        fig = px.bar(top, x="route_id", y=sort_col, color="city", title=f"Top Routes by {sort_col.replace('_', ' ').title()}")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Route records")
        st.dataframe(filtered.sort_values(sort_col, ascending=False), use_container_width=True)

elif page == "Clustering Results":
    st.title("K-Means and DBSCAN Clustering")
    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    if route_table.empty:
        st.warning("No route data is available for clustering.")
    else:
        feature_options = [c for c in ["trip_frequency", "total_scheduled_trips", "peak_hour_trips", "avg_hourly_trips", "peak_hour_ratio"] if c in route_table]
        features = st.multiselect("Clustering features", feature_options, default=["trip_frequency", "peak_hour_ratio"])
        k = st.slider("K-Means cluster count", 2, 8, 3)

        if len(features) >= 2:
            cluster_df = route_table[["city", "route_id"] + features].dropna(subset=features).copy()
            cluster_df = build_cluster_table(cluster_df, tuple(features), k)

            x_col, y_col = features[0], features[1]
            c1, c2 = st.columns(2)
            with c1:
                fig = px.scatter(cluster_df, x=x_col, y=y_col, color=cluster_df["KMeans_Cluster"].astype(str), title="K-Means Cluster Assignment", hover_data=["route_id", "city"])
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig = px.scatter(cluster_df, x=x_col, y=y_col, color=cluster_df["DBSCAN_Cluster"].astype(str), title="DBSCAN (DBSCAN noise is labeled -1)", hover_data=["route_id", "city"])
                st.plotly_chart(fig, use_container_width=True)

            selected_k = st.selectbox("Filter K-Means cluster", sorted(cluster_df["KMeans_Cluster"].unique()))
            st.dataframe(cluster_df[cluster_df["KMeans_Cluster"] == selected_k].sort_values(features[0], ascending=False), use_container_width=True)
            st.caption("Clusters are descriptive groups of similar routes; they do not confirm efficiency or inefficiency.")

elif page == "Model Predictions":
    st.title("Random Forest Prediction Results")
    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    predictions, error = get_model_predictions(route_table)

    if error:
        st.error(error)
    elif predictions.empty:
        st.warning("No prediction records are available.")
    else:
        predicted = predictions
        c1, c2, c3 = st.columns(3)
        counts = predicted["RF_Predicted_Category"].value_counts()
        c1.metric("Balanced", int(counts.get("Balanced", 0)))
        c2.metric("Moderate", int(counts.get("Moderate", 0)))
        c3.metric("Overcrowded", int(counts.get("Overcrowded", 0)))

        city = st.selectbox("City", ["All"] + sorted(predicted["city"].dropna().astype(str).unique()))
        filtered = predicted if city == "All" else predicted[predicted["city"] == city]
        category = st.selectbox("Predicted category", ["All"] + sorted(filtered["RF_Predicted_Category"].dropna().unique()))
        if category != "All":
            filtered = filtered[filtered["RF_Predicted_Category"] == category]

        fig = px.histogram(filtered, x="RF_Predicted_Category", color="RF_Predicted_Category", title="Random Forest Predicted Categories")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Route-level predictions")
        st.dataframe(filtered[[c for c in ["city", "route_id", "route_short_name", "route_long_name", "trip_frequency", "total_scheduled_trips", "peak_hour_ratio", "RF_Predicted_Category", "RF_Confidence"] if c in filtered]], use_container_width=True)

    st.caption("XGBoost is not represented because no trained XGBoost artifact is available in this workspace.")

elif page == "Route Optimization":
    st.title("Route Optimization Recommendations")
    st.info("These are proposed or simulated changes, not confirmed operational improvements.")

    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    recommendations, error = build_dynamic_recommendations(route_table)

    if error:
        st.error(error)
    elif recommendations.empty:
        st.warning("No uploaded or existing route records are available for recommendation generation.")
    else:
        st.subheader("Trip Frequency Adjustment")
        rec_counts = recommendations["Advanced_Recommendation"].value_counts().reset_index()
        rec_counts.columns = ["Recommendation", "Routes"]
        fig = px.bar(rec_counts, x="Recommendation", y="Routes", title="Recommendation Distribution")
        st.plotly_chart(fig, use_container_width=True)

        recommendation = st.selectbox("Filter recommendation", ["All"] + sorted(recommendations["Advanced_Recommendation"].dropna().unique()))
        filtered = recommendations if recommendation == "All" else recommendations[recommendations["Advanced_Recommendation"] == recommendation]
        st.dataframe(filtered, use_container_width=True)

        lower = recommendations["Advanced_Recommendation"].str.lower()
        merge_count = lower.str.contains("merg", na=False).sum()
        split_count = lower.str.contains("splitt", na=False).sum()
        frequency_count = lower.str.contains("frequency|extra trip|schedule adjustment", regex=True, na=False).sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Possible merging candidates", int(merge_count))
        c2.metric("Splitting scenarios", int(split_count))
        c3.metric("Frequency adjustment scenarios", int(frequency_count))

elif page == "Metrics Comparison":
    st.title("Current vs. Simulated Metrics")
    route_table = build_route_table(data["route_frequency"], data["hourly"], data["routes"])
    predictions, error = get_model_predictions(route_table)

    if error:
        st.error(error)
    elif predictions.empty:
        st.warning("No active route records are available for comparison.")
    else:
        comparison = build_dynamic_comparison(predictions)

        before_total = int(comparison["Before_Optimization"].sum())
        after_total = int(comparison["After_Optimization"].sum())
        c1, c2 = st.columns(2)
        c1.metric("Before: modeled routes", before_total)
        c2.metric("After: simulated routes", after_total)

        fig = px.bar(comparison, x="Performance", y=["Before_Optimization", "After_Optimization"], barmode="group", title="Before vs. After Simulated Route Categories")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comparison, use_container_width=True)

        st.caption("The simulation moves 20% of predicted overcrowded routes to balanced for the active dataset. It does not calculate passenger counts or validate stop coverage.")

else:
    st.title("About / Project Information")
    st.subheader("Methodology")
    st.write("GTFS data is integrated and cleaned, route trip frequencies and hourly frequencies are calculated, route features are analyzed, clustering is recomputed, and a saved Random Forest model is used for route-category predictions.")

    st.subheader("Technologies")
    st.write("Python, Pandas, NumPy, Streamlit, Plotly, scikit-learn, Joblib, and GTFS CSV data.")

    st.subheader("Important Limitations")
    st.warning("• Passenger demand and actual ridership are not assumed from scheduled trips.\n• Clusters are descriptive and not labels of route efficiency.\n• Optimization recommendations are simulated proposals.\n• No saved XGBoost model is available in the workspace.\n• Stop coverage and passenger-demand evidence are required before real-world implementation.")

    st.subheader("Source Files")
    st.code("routes.csv, trips.csv, stop_times.csv, stops.csv, route_trip_frequency.csv, hourly_route_frequency.csv, route_optimization_recommendations.csv, route_optimization_comparison.csv")
