"""RouteRanker - interactive dashboard (Module 7).   Run with:  streamlit run app.py

Brings together Modules 1-6: dataset, EDA, KMeans / DBSCAN results, Random Forest / XGBoost predictions, optimisation suggestions and a current-vs-simulated
comparison. Everything shown is read from, or computed with, the project's own files and saved models - nothing is typed in.
GTFS contains scheduled service only: no passenger counts exist, so no route is called overcrowded or inefficient anywhere in this app."""
import platform

import numpy as np
import pandas as pd
import streamlit as st

from modules import clustering, data_loader as dl, data_validation as dv, optimization as mopt, predictions as pred, route_analysis as ra, visualizations as viz
from src import eda, inference as inf, optimization as opt

st.set_page_config(page_title="RouteRanker", page_icon="🚌", layout="wide")
SECTIONS = ["1. Home / Project Overview", "2. Dataset Overview", "3. Exploratory Data Analysis", "4. Route Analysis", "5. Clustering Results",
            "6. Model Predictions", "7. Route Optimization", "8. Metrics Comparison", "9. About / Project Information"]
KIND = {"actual": ":blue[ACTUAL - scheduled GTFS data]", "predicted": ":orange[MODEL PREDICTION]", "estimated": ":violet[ESTIMATE]", "simulated": ":red[SIMULATED / PROPOSED - not validated]"}
NUMERIC_FEATURES = ["n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_speed_kmh", "max_stop_overlap", "trips_per_active_hour"]
_key = iter(range(10_000))
nk = lambda: f"k{next(_key)}"                    # unique widget / chart keys


def chart(fig):
    st.plotly_chart(fig, width="stretch", key=nk())


def show(df, **kw):
    st.dataframe(df, width="stretch", hide_index=kw.pop("hide_index", True), **kw)


# ------------------------------------------------------------------ guard: all project outputs must exist
missing = dl.missing_files()
if missing:
    st.title("🚌 RouteRanker")
    st.error("Some project files that the dashboard needs are missing. Create them by running the module scripts first:")
    show(pd.DataFrame({"missing": list(missing), "expected file": list(missing.values())}))
    st.code("python run_module2.py\npython run_module4.py\npython run_module5.py\npython run_module6.py")
    st.stop()

# ------------------------------------------------------------------ sidebar
st.sidebar.title("🚌 RouteRanker")
section = st.sidebar.radio("Navigate", SECTIONS)
comparable = [c for c in dl.CITIES if c not in dl.EXCLUDED_FEEDS]
sel_cities = st.sidebar.multiselect("Cities in scope", dl.CITIES, default=comparable, help="Hyderabad is excluded by default: its 'trips' look like whole vehicle duties, so it is not comparable with the other feeds.")
if not sel_cities:
    st.warning("Select at least one city in the sidebar.")
    st.stop()
if set(sel_cities) & set(dl.EXCLUDED_FEEDS):
    st.sidebar.warning("Hyderabad is selected: its trip counts, headways and speeds are not comparable with the other cities.")
st.sidebar.caption("Colour code used everywhere:")
for v in KIND.values():
    st.sidebar.markdown(v)

ROUTES = dl.load_routes()
routes = ROUTES[ROUTES.city.isin(sel_cities)]


def hours_for(city):
    return dl.load_route_hours(city)


# ================================================================== 1. HOME
def page_home():
    st.title("🚌 RouteRanker – AI-Powered Public Transit Route Optimization")
    st.markdown("**Objective:** analyse the *scheduled* bus service of Indian cities, group routes with similar service patterns, find routes that may deserve a closer look and explore "
                "*possible* merge / split / frequency changes - and compare the current network with a simulated one.")
    st.info("GTFS describes **planned** service. It contains **no passenger counts or occupancy**, so this dashboard never claims that a route is overcrowded, underutilised or inefficient. "
            "Suggestions are candidates to verify; simulated results are what-if scenarios, not forecasts.")
    stops_total = sum(len(dl.load_stops(c)) for c in dl.CITIES)
    c = st.columns(5)
    c[0].metric("Routes", f"{len(ROUTES):,}")
    c[1].metric("Cities (open GTFS feeds)", ROUTES.city.nunique())
    c[2].metric("Scheduled trips", f"{int(ROUTES.n_trips.sum()):,}")
    c[3].metric("Stops", f"{stops_total:,}")
    c[4].metric("Route features", ROUTES.shape[1])
    st.caption(f"{KIND['actual']} - counts of the collected feeds (7 of the 23 planned cities: the Lepton/Datarade dataset is a paid listing and could not be obtained).")
    st.subheader("What the dashboard contains")
    show(pd.DataFrame([
        ["1-2", "Data collection, feature engineering", "Dataset Overview, Route Analysis"], ["3", "Exploratory data analysis", "Exploratory Data Analysis"],
        ["4-5", "Preprocessing, KMeans / DBSCAN / Random Forest / XGBoost", "Clustering Results, Model Predictions"],
        ["6", "Inference, route-optimisation suggestions, simulation", "Route Optimization, Metrics Comparison"]], columns=["Modules", "Work", "Dashboard section"]))
    st.subheader("Key facts computed from the data")
    p = dl.load_predictions()
    new = p[p.data_role.str.startswith("unseen")]
    comp = ROUTES[~ROUTES.city.isin(dl.EXCLUDED_FEEDS)]
    st.markdown(f"* {100 * (comp.n_trips <= 5).mean():.0f}% of routes in the comparable cities have 5 or fewer scheduled trips, while the busiest route has {int(comp.n_trips.max()):,}: service levels differ widely.\n"
                f"* {100 * (new.dbscan_label == -1).mean():.0f}% of the unseen Hyderabad routes are DBSCAN noise (training routes: {100 * (p[p.data_role.str.startswith('train')].dbscan_label == -1).mean():.1f}%): that feed is not comparable.\n"
                f"* Different cities can be told apart from schedule features alone - each feed has its own 'fingerprint', so compare routes within a city.")
    st.subheader("How to use it")
    st.markdown("Pick a section in the sidebar. Use *Cities in scope* to restrict every page. In **Route Optimization** open *What-if thresholds* to change the rules and watch the suggestions and the "
                "comparison update. Upload your own route table in **Dataset Overview → Upload**.")


# ================================================================== 2. DATASET
def page_dataset():
    st.header("Dataset Overview")
    st.caption(f"{KIND['actual']} - `data/processed/all_cities_route_features.csv` (Module 2: one row per route, built from routes, trips, stop_times, stops and calendar).")
    t1, t2, t3, t4 = st.tabs(["Overview", "Data quality", "Filter & explore", "Upload your own routes"])
    with t1:
        c = st.columns(4)
        c[0].metric("Records (routes)", f"{len(routes):,}")
        c[1].metric("Features (columns)", routes.shape[1])
        c[2].metric("Cities", routes.city.nunique())
        c[3].metric("Scheduled trips", f"{int(routes.n_trips.sum()):,}")
        view = st.radio("Preview", ["first 50 records", "last 50 records", "random 50 records"], horizontal=True)
        show(routes.head(50) if view.startswith("first") else routes.tail(50) if view.startswith("last") else routes.sample(min(50, len(routes)), random_state=1))
        st.subheader("Column names and data types")
        show(dv.schema_table(routes))
        st.subheader("Descriptive statistics (numeric columns)")
        st.dataframe(dv.numeric_summary(routes), width="stretch")
    with t2:
        st.markdown("Problems are **reported, not silently changed or deleted**. Missing values are *undefined* (for example no headway when a route has one departure) - they are never replaced by zero.")
        show(dv.quality_report(routes))
        sc = dv.schema_table(routes)
        st.subheader("Columns with missing values")
        show(sc[sc.missing > 0])
        st.caption("`length_km_shape` is empty for feeds without shapes.txt (length then comes from stop coordinates, see `length_method`); `n_directions` where a feed has no direction_id.")
    with t3:
        c = st.columns(3)
        tmax = int(routes.n_trips.max())
        trips = c[0].slider("Scheduled trips per route", 1, tmax, (1, tmax))
        lmax = float(np.ceil(routes.length_km.max()))
        length = c[1].slider("Estimated length (km)", 0.0, lmax, (0.0, lmax))
        q = c[2].text_input("Route name contains")
        f = ra.filter_routes(routes, sel_cities, trips, length, q)
        st.write(f"**{len(f):,}** of {len(routes):,} routes match")
        cols = st.multiselect("Columns to show", list(f.columns), default=["city", "route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "length_method", "service_span_h", "median_headway_min"])
        show(f[cols].head(1000) if cols else f.head(1000))
        st.download_button("Download the filtered table (CSV)", f.to_csv(index=False), "filtered_routes.csv", "text/csv")
    with t4:
        st.markdown("Upload a route table (CSV or Excel) with the **Module-2 feature columns** (a ready template is below). The app validates it and can apply the **saved** models to it - "
                    "the same preprocessing as in training is used and nothing is re-fitted.")
        st.download_button("Download a template (20 real rows)", ROUTES.head(20).to_csv(index=False), "route_features_template.csv", "text/csv")
        up = st.file_uploader("Route table", type=["csv", "xlsx", "xls"])
        if up is not None:
            df, err = dv.read_upload(up)
            if err:
                st.error(err)
            else:
                st.success(f"Read {len(df):,} rows and {df.shape[1]} columns.")
                show(df.head(20))
                ok, msg = dv.validate_for_inference(df)
                with st.expander("Validation and data quality", expanded=not ok):
                    (st.success if ok else st.error)(msg)
                    show(dv.schema_table(df))
                    if ok:
                        show(dv.quality_report(df))
                if ok and st.button("Run the saved models on this table"):
                    models = dl.load_models()
                    names = clustering.kmeans_profile().description.to_dict()
                    _, _, out = inf.run_inference(df, models, names)
                    st.caption(f"{KIND['predicted']} - KMeans nearest centroid, DBSCAN nearest core point within eps (otherwise noise), XGBoost closest known feed.")
                    show(out)
                    st.download_button("Download predictions (CSV)", out.to_csv(index=False), "uploaded_routes_predictions.csv", "text/csv")


# ================================================================== 3. EDA
def page_eda():
    st.header("Exploratory Data Analysis")
    st.caption(f"{KIND['actual']} - all charts show **scheduled service supply**, not passenger demand.")
    t = st.tabs(["Distributions", "Scheduled trips by hour", "Route comparison", "Correlation", "Geography"])
    with t[0]:
        c = st.columns(3)
        feat = c[0].selectbox("Feature", NUMERIC_FEATURES, key="eda_feat")
        logx = c[1].checkbox("Log scale", value=feat in ("n_trips", "n_unique_stops", "length_km", "median_headway_min"))
        by_city = c[2].checkbox("Colour by city", value=False)
        chart(viz.hist_fig(routes, feat, "city" if by_city else None, logx))
        chart(viz.box_fig(routes, feat, log_y=logx))
        for line in eda.obs_univariate(routes):
            st.markdown(f"* {line}")
    with t[1]:
        city = st.selectbox("City", sel_cities, key="eda_hour_city")
        rh = hours_for(city)
        h, p = eda.hourly_table(rh), eda.period_table(eda.hourly_table(rh))
        cols = {"scheduled_trips": "all scheduled trips"}
        if "trips_weekday_wed" in h and h.trips_weekday_wed.sum() != h.trips_sunday.sum():
            cols = {"trips_weekday_wed": "typical weekday (Wednesday services)", "trips_sunday": "Sunday services"}
        chart(viz.hourly_fig(h.reset_index().rename(columns={"index": "hour"}), cols, f"{city.title()}: scheduled trips starting in each clock hour"))
        chart(viz.period_fig(p.reset_index(), f"{city.title()}: scheduled trips by time period"))
        for line in eda.obs_hourly(h, p):
            st.markdown(f"* {line}")
        st.caption("Periods: morning 05:00-11:59, afternoon 12:00-16:59, evening 17:00-20:59, night 21:00-04:59.")
    with t[2]:
        c = st.columns(2)
        by = c[0].selectbox("Rank routes by", ["n_trips", "n_unique_stops", "length_km", "service_span_h"], key="eda_rank")
        n = c[1].slider("How many routes", 5, 40, 15)
        chart(viz.top_routes_fig(routes, n, by))
        st.subheader("Routes grouped by scheduled trips")
        show(ra.group_comparison(routes))
        st.markdown("Routes with few or many scheduled trips differ in other ways too, but this describes the **timetable** - it does not show that a route is efficient or not. "
                    "Ridership, capacity and operating data would be needed for that.")
        c = st.columns(3)
        x = c[0].selectbox("x axis", NUMERIC_FEATURES, index=2, key="sx")
        y = c[1].selectbox("y axis", NUMERIC_FEATURES, index=0, key="sy")
        col = c[2].checkbox("Colour by city", value=True, key="scol")
        chart(viz.scatter_fig(routes, x, y, "city" if col else None, log_y=y in ("n_trips", "n_unique_stops", "length_km")))
    with t[3]:
        feats = st.multiselect("Features", NUMERIC_FEATURES + ["stops_per_km", "mean_routes_per_stop"], default=NUMERIC_FEATURES[:6], key="corr_feats")
        if len(feats) >= 2:
            chart(viz.corr_fig(routes, feats))
            for line in eda.obs_corr(routes):
                st.markdown(f"* {line}")
            st.caption("Correlation shows association, not cause. Scheduled trips, trips per active hour, headway and service span are linked by definition, so their strong correlation is expected.")
        else:
            st.info("Select at least two features.")
    with t[4]:
        city = st.selectbox("City", sel_cities, key="geo_city")
        stops = dl.load_stops(city)
        if stops.empty or stops[["stop_lat", "stop_lon"]].dropna().empty:
            st.warning("No valid stop coordinates for this city - no map is drawn.")
        else:
            chart(viz.stops_map_fig(stops, city))
            st.subheader("Stops served by the most routes")
            show(stops.nlargest(15, "n_routes")[["stop_name", "n_routes", "scheduled_visits", "peak_hour"]])
            st.caption("Route paths and shape-based overlap maps are in `reports/maps/` (Module 3). Two routes sharing stops are not necessarily redundant.")


# ================================================================== 4. ROUTE ANALYSIS
def page_routes():
    st.header("Route Analysis")
    st.caption(f"{KIND['actual']} profile of one route (scheduled service). {KIND['estimated']} for route length and speed.")
    c = st.columns([1, 1, 2])
    city = c[0].selectbox("City", sel_cities, key="ra_city")
    q = c[1].text_input("Search route name", key="ra_q")
    g = routes[routes.city == city]
    g = g[g.route_name.astype(str).str.contains(q, case=False, regex=False)] if q else g
    if g.empty:
        st.info("No route matches.")
        return
    g = g.sort_values("n_trips", ascending=False).head(800)
    opts = {f"{r.route_name}  (id {r.route_id}, {int(r.n_trips)} trips)": r.route_id for r in g.itertuples()}
    rid = opts[c[2].selectbox("Route (sorted by scheduled trips)", list(opts), key="ra_route")]
    r = g[g.route_id == rid].iloc[0]
    m = st.columns(5)
    m[0].metric("Scheduled trips", int(r.n_trips))
    m[1].metric("Distinct stops", int(r.n_unique_stops))
    m[2].metric("Est. length (km)", f"{r.length_km:.1f}")
    m[3].metric("Service span (h)", f"{r.service_span_h:.1f}")
    m[4].metric("Median headway (min)", "n/a" if pd.isna(r.median_headway_min) else f"{r.median_headway_min:.0f}")
    st.caption(f"Length method: **{r.length_method}**. A missing headway means the route has a single departure time (undefined, not zero).")
    chart(viz.route_hours_fig(ra.hourly_for_route(hours_for(city), city, rid), title=f"Route {r.route_name}: scheduled trips by clock hour"))
    st.subheader("Where this route stands among the routes of its city")
    show(ra.peer_percentiles(ROUTES, city, rid))
    with st.expander("All features of this route"):
        show(r.to_frame("value").reset_index().rename(columns={"index": "feature"}).astype(str))
    st.subheader("Compare with another route")
    other = opts[st.selectbox("Second route", list(opts), index=min(1, len(opts) - 1), key="ra_route2")]
    r2 = g[g.route_id == other].iloc[0]
    cols = ["route_name", "n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_speed_kmh", "max_stop_overlap", "trips_morning", "trips_afternoon", "trips_evening", "trips_night"]
    show(pd.DataFrame({"feature": cols, f"route {r.route_name}": [r[c] for c in cols], f"route {r2.route_name}": [r2[c] for c in cols]}).astype(str))
    st.caption("A difference in scheduled trips is a reason to look closer, not proof of inefficiency: passenger demand, capacity and the route's purpose are unknown.")


# ================================================================== 5. CLUSTERS
def page_clusters():
    st.header("Clustering Results")
    emb = clustering.embedding()
    st.info("A cluster is a group of routes with **similar scheduled service**. Cluster numbers are not rankings; a cluster is **not** 'efficient' or 'inefficient' and not a recommendation.")
    roles = sorted(emb.data_role.unique())
    c = st.columns([2, 3])
    show_roles = c[0].multiselect("Data", roles, default=[r for r in roles if not r.startswith("unseen")], help="'unseen feed' = Hyderabad, not part of the training set.")
    d = emb[emb.city.isin(sel_cities) & emb.data_role.isin(show_roles)]
    if d.empty:
        st.info("No routes in this selection.")
        return
    c[1].caption(f"{KIND['predicted']} - KMeans (K={d.kmeans_cluster.nunique()}) and DBSCAN trained in Module 5 and applied to every route in Module 6. {len(d):,} routes selected.")
    t = st.tabs(["KMeans", "DBSCAN", "KMeans vs DBSCAN"])
    with t[0]:
        prof = clustering.kmeans_profile()
        st.subheader("What each cluster looks like (median of the original, unscaled features)")
        show(prof.reset_index())
        picks = st.multiselect("Show clusters", sorted(d.kmeans_cluster.unique()), default=sorted(d.kmeans_cluster.unique()), format_func=lambda k: f"{k}: {prof.description.get(k, '')}", key="km_pick")
        s = d[d.kmeans_cluster.isin(picks)]
        if s.empty:
            st.info("Select at least one cluster.")
        else:
            s = s.assign(cluster=s.kmeans_cluster.astype(str))
            chart(viz.pca_fig(s, "cluster", f"KMeans clusters in a 2-D PCA projection ({100 * emb.attrs.get('explained', 0):.0f}% of variance; the model uses all 25 features)"))
            chart(viz.share_bar_fig(s, "cluster", "city", "Which cities make up each cluster (a cluster dominated by one city partly reflects that feed's style)"))
            feats = [f for f in clustering.FEATURES if f in s]
            z = (s[feats] - d[feats].mean()) / d[feats].std()
            chart(viz.profile_heatmap(z.groupby(s.cluster.values).mean().round(2), "Mean standardised feature value per cluster (red = above average, blue = below)"))
            f1 = st.selectbox("Compare clusters on", feats, key="km_cmp")
            chart(viz.box_fig(s.assign(cluster=s.cluster), f1, by="cluster", log_y=f1 in ("n_trips", "n_unique_stops", "length_km")))
            st.subheader("Routes in the selected clusters")
            show(s[["city", "route_id", "route_name", "kmeans_cluster", "kmeans_cluster_description", "n_trips", "n_unique_stops", "length_km", "dist_to_centroid"]].head(1000))
            st.download_button("Download these routes (CSV)", s.drop(columns=["cluster"]).to_csv(index=False), "kmeans_routes.csv", "text/csv")
    with t[1]:
        sm = clustering.dbscan_summary(emb)
        st.subheader("Share of routes labelled noise, by data role")
        show(sm)
        st.markdown("DBSCAN marks routes that sit in no dense region as **noise (-1)**. In Module 5 it found one very large dense cluster and few unusual routes, so it is most useful for **finding unusual routes**. "
                    "Noise is not an error: it may be a data problem, a special service or a rare but normal combination of values.")
        chart(viz.pca_fig(d, "dbscan_group", "DBSCAN labels in the same 2-D projection (noise = unusual for the training data)"))
        nz = d[d.dbscan_label == -1]
        c = st.columns(2)
        c[0].metric("Noise routes in this selection", f"{len(nz):,}", f"{100 * len(nz) / len(d):.1f}% of routes", delta_color="off")
        by = nz.groupby("city").size().rename("noise routes").reset_index()
        if len(by):
            c[1].dataframe(by, hide_index=True)
        if len(nz):
            cmp_ = pd.DataFrame({"noise routes (median)": nz[clustering.FEATURES].median(), "other routes (median)": d[d.dbscan_label != -1][clustering.FEATURES].median()}).round(2)
            st.subheader("Noise routes versus the rest")
            show(cmp_.reset_index().rename(columns={"index": "feature"}))
            st.subheader("The noise routes")
            show(nz[["city", "route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "dist_to_nearest_core"]].sort_values("dist_to_nearest_core", ascending=False).head(500))
    with t[2]:
        ct = pd.crosstab(d.kmeans_cluster, d.dbscan_group)
        st.markdown("Routes by KMeans cluster (rows) and DBSCAN label (columns):")
        show(ct.reset_index())
        st.caption("KMeans assigns every route to a cluster; DBSCAN keeps most routes in one dense region and flags a few as noise - the two answer different questions.")


# ================================================================== 6. PREDICTIONS
def page_predictions():
    st.header("Model Predictions")
    st.info("Random Forest and XGBoost were trained in Module 5 to predict the **city** of a route - the only real label in GTFS-based data. GTFS has no passenger or performance labels, "
            "so these models do **not** predict overcrowding, demand or route quality. The result tells how closely a route's schedule features resemble each known feed.")
    t = st.tabs(["Evaluation of the saved models", "Predict for one route", "Prediction table"])
    cls = pred.classes()
    with t[0]:
        res, cms, per = pred.validation_evaluation()
        st.caption(f"{KIND['predicted']} - evaluated live on the held-out validation routes (never used for training).")
        show(res)
        c = st.columns(2)
        for col, name in zip(c, ("XGBoost", "Random Forest")):
            with col:
                chart(viz.confusion_fig(cms[name], cls, f"{name}: confusion matrix (validation routes)"))
        which = st.selectbox("Per-city precision / recall / F1", list(per), key="pc_model")
        show(per[which])
        st.markdown("Both models separate the cities very well, so the feeds differ in how their schedules are written - **a high score here is not a sign of a good route model.**")
    with t[1]:
        c = st.columns([1, 1, 2])
        city = c[0].selectbox("City", sel_cities, key="pr_city")
        q = c[1].text_input("Search route name", key="pr_q")
        g = routes[routes.city == city]
        g = g[g.route_name.astype(str).str.contains(q, case=False, regex=False)] if q else g
        if g.empty:
            st.info("No route matches.")
        else:
            g = g.sort_values("n_trips", ascending=False).head(500)
            opts = {f"{r.route_name}  (id {r.route_id})": r.route_id for r in g.itertuples()}
            rid = opts[c[2].selectbox("Route", list(opts), key="pr_route")]
            row = g[g.route_id == rid].head(1)
            out = pred.predict_routes(row)
            x = out[out.model == "XGBoost"].iloc[0]
            rf_ = out[out.model == "Random Forest"].iloc[0]
            m = st.columns(4)
            m[0].metric("Actual city", city.title())
            m[1].metric("XGBoost: closest feed", x.predicted_feed.title(), f"confidence {x.confidence:.2f}", delta_color="off")
            m[2].metric("Random Forest: closest feed", rf_.predicted_feed.title(), f"confidence {rf_.confidence:.2f}", delta_color="off")
            m[3].metric("Models agree", "yes" if x.predicted_feed == rf_.predicted_feed else "no")
            chart(viz.proba_fig(out, cls, "Predicted probability per city (each model)"))
            show(out.reset_index(drop=True))
            if city in dl.EXCLUDED_FEEDS:
                st.warning("This city was not part of the models' training data, so the prediction only shows which *known* feed it resembles most.")
    with t[2]:
        p = dl.load_predictions()
        p = p[p.city.isin(sel_cities)]
        c = st.columns(2)
        roles = c[0].multiselect("Data", sorted(p.data_role.unique()), default=sorted(p.data_role.unique()), key="pt_roles")
        feeds = c[1].multiselect("Closest known feed (XGBoost)", sorted(p.closest_known_feed.unique()), default=sorted(p.closest_known_feed.unique()), key="pt_feeds")
        f = p[p.data_role.isin(roles) & p.closest_known_feed.isin(feeds)]
        st.write(f"{len(f):,} routes. Share where the closest feed equals the actual city: **{100 * (f.closest_known_feed == f.city).mean():.1f}%**")
        show(f.head(1000))
        st.download_button("Download (CSV)", f.to_csv(index=False), "predictions.csv", "text/csv")


# ================================================================== 7. OPTIMIZATION
def get_params():
    d = mopt.DEFAULTS
    with st.expander("What-if thresholds (defaults = the rules used in Module 6)"):
        c = st.columns(4)
        p = dict(
            jac_min=c[0].slider("Merge: min. stop-set similarity", 0.5, 1.0, float(d["jac_min"]), 0.05),
            low_q=c[1].slider("Merge: 'lightly scheduled' = lowest share of city", 0.05, 0.5, float(d["low_q"]), 0.05),
            len_ratio=c[2].slider("Merge: max length ratio", 1.1, 3.0, float(d["len_ratio"]), 0.1),
            min_km=c[3].slider("Split: min. length (km)", 20, 100, int(d["min_km"]), 5))
        c = st.columns(4)
        p.update(len_q=c[0].slider("Split: within the longest share of the city's routes", 0.5, 0.99, float(d["len_q"]), 0.01),
                 min_stops=c[1].slider("Split: min. stops", 10, 100, int(d["min_stops"]), 5),
                 min_trips=c[2].slider("Frequency: min. scheduled trips", 2, 30, int(d["min_trips"]), 1),
                 standard=c[3].slider("Frequency: maximum headway in the busiest hour (min)", 10, 60, int(d["standard"]), 5))
        st.caption("These thresholds are rules of thumb, not operator standards; changing them changes the counts. The 30-minute headway standard is an assumption, not demand evidence.")
    params = tuple(p[k] for k in d)
    st.session_state["opt_params"] = params
    return params, params == tuple(d.values())


def page_optimization():
    st.header("Route Optimization")
    st.warning("**Candidates to verify, not recommendations.** No passenger demand, capacity or travel-time data exists in GTFS. "
               "Suggestions come from schedule and shared-stop geography only; every simulated change is a what-if, not a confirmed improvement. Hyderabad is excluded (not comparable).")
    params, is_default = get_params()
    ev, mg, sp, fq = mopt.candidates(params)
    st.caption(("Using the **Module 6 default rules**." if is_default else "Using **your what-if thresholds**.") + f" {KIND['estimated']} (rules applied to {KIND['actual']}).")
    c = st.columns(4)
    c[0].metric("Routes with ≥ 2 evidence flags", f"{int((ev.n_evidence >= 2).sum()):,}")
    c[1].metric("Merge candidates", f"{len(mg):,}")
    c[2].metric("Split candidates", f"{len(sp):,}")
    c[3].metric("Frequency-standard candidates", f"{len(fq):,}")
    t = st.tabs(["Routes to investigate", "Route merging", "Route splitting", "Trip frequency"])
    cities = [c for c in sel_cities if c not in dl.EXCLUDED_FEEDS]
    with t[0]:
        st.markdown("A route is listed only when **independent pieces of evidence agree** (never one feature or one cluster alone): DBSCAN noise, membership of a KMeans cluster of very few trips, "
                    "shared stops with another route, few trips compared with routes of similar length.")
        k = st.slider("Minimum number of evidence flags", 1, 4, 2)
        d = ev[ev.city.isin(cities) & (ev.n_evidence >= k)].copy()
        d["why listed"] = mopt.evidence_text(d)
        st.write(f"**{len(d):,}** routes")
        show(d.sort_values("n_evidence", ascending=False)[["city", "route_id", "route_name", "n_evidence", "why listed", "n_trips", "n_unique_stops", "length_km", "data_check_first"]].head(1000))
        st.caption("`data_check_first` = impossible scheduled speed: check the data (length or timetable) before anything else.")
        chart(viz.share_bar_fig(ev[ev.city.isin(cities)].assign(flags=ev.n_evidence.astype(str)), "city", "flags", "Share of routes by number of evidence flags"))
    with t[1]:
        st.markdown(f"**Rule:** route r may be merged into its best stop-sharing partner p when they have different line names (not opposite directions), their stop sets are ≥ {params[0]:.0%} similar "
                    f"(geographical connectivity), r is lightly scheduled and the lengths are similar. Each route is used once.")
        m = mg[mg.city.isin(cities)] if len(mg) else mg
        if m.empty:
            st.info("No merge candidates for these settings and cities.")
        else:
            show(m[["city", "absorbed_route", "target_route", "stop_overlap_jaccard", "trips_absorbed", "trips_target", "length_absorbed_km", "length_target_km"]].head(1000))
            idx = st.selectbox("Examine a possible merge", list(range(min(len(m), 300))), format_func=lambda i: f"{m.iloc[i].city}: {m.iloc[i].absorbed_route} → {m.iloc[i].target_route}  (overlap {m.iloc[i].stop_overlap_jaccard:.0%})", key="mg_pick")
            row = m.iloc[idx]
            st.caption(KIND["simulated"] + " - the absorbed route's departures are kept; its unshared stretch is added to the target route.")
            show(mopt.merge_preview(row).fillna("").astype(str))
            hh = hours_for(row.city)
            c = st.columns(2)
            with c[0]:
                chart(viz.route_hours_fig(ra.hourly_for_route(hh, row.city, row.target_route_id), title=f"Target route {row.target_route}: scheduled trips by hour"))
            with c[1]:
                chart(viz.route_hours_fig(ra.hourly_for_route(hh, row.city, row.absorbed_route_id), title=f"Route {row.absorbed_route} (would be merged)"))
            st.markdown("**Verify before merging:** passenger demand on both routes, vehicle capacity, travel time, whether the unshared stops stay covered (the simulation keeps them), and whether the routes serve different purposes (e.g. express vs local).")
    with t[2]:
        st.markdown(f"**Rule:** a route is a split candidate when it is long (≥ {params[3]} km and among the longest {1 - params[4]:.0%} of its city) and complex (≥ {params[5]} stops) with a plausible scheduled speed.")
        s = sp[sp.city.isin(cities)] if len(sp) else sp
        if s.empty:
            st.info("No split candidates for these settings and cities.")
        else:
            s = s.sort_values("length_km", ascending=False).reset_index(drop=True)
            show(s[["city", "route", "length_km", "length_method", "stops", "trips", "service_span_h"]].head(1000))
            i = st.selectbox("Examine a possible split", list(range(min(len(s), 300))), format_func=lambda i: f"{s.iloc[i].city}: {s.iloc[i].route} ({s.iloc[i].length_km:.0f} km)", key="sp_pick")
            r = s.iloc[i]
            st.caption(KIND["simulated"] + " - cut at the middle stop; each part keeps all original departures, so scheduled trip-km is unchanged while trip records double (transfer burden ignored).")
            show(pd.DataFrame({"": ["estimated length (km)", "distinct stops", "scheduled trips"], f"current route {r.route}": [r.length_km, r.stops, r.trips],
                               "part A (SIMULATED)": [round(r.length_km / 2, 1), int(np.ceil(r.stops / 2)) + 1, r.trips], "part B (SIMULATED)": [round(r.length_km / 2, 1), int(np.ceil(r.stops / 2)) + 1, r.trips]}).astype(str))
            if r.length_method != "shapes.txt":
                st.caption("The length comes from stop coordinates (a straight-line lower bound), so the route may be even longer.")
            st.markdown("**Verify before splitting:** passenger journey lengths, where the transfer would be and its burden, travel time and connectivity between the parts.")
    with t[3]:
        st.markdown(f"**What the data supports:** a *service-standard* check. Routes with ≥ {params[6]} scheduled trips but a headway above **{params[7]} minutes even in their busiest hour** "
                    f"(fewer than {int(np.ceil(60 / params[7]))} departures) are listed; adding departures to reach the standard is **simulated**. The standard is our assumption, not demand evidence, "
                    "and **no trip reductions are suggested**: without demand data we cannot know which trips are unnecessary.")
        f = fq[fq.city.isin(cities)] if len(fq) else fq
        if f.empty:
            st.info("No routes fall below the standard for these settings and cities.")
        else:
            st.write(f"**{len(f):,}** routes; **{int(f.trips_to_add.sum()):,}** trips would be added to reach the standard.")
            show(f[["city", "route", "trips", "peak_hour", "departures_in_peak_hour", "trips_to_add"]].head(1000))
            i = st.selectbox("Examine a route", list(range(min(len(f), 300))), format_func=lambda i: f"{f.iloc[i].city}: {f.iloc[i].route} ({int(f.iloc[i].trips)} trips)", key="fq_pick")
            r = f.iloc[i]
            h = ra.hourly_for_route(hours_for(r.city), r.city, r.route_id)
            chart(viz.route_hours_fig(h, (int(r.peak_hour), int(r.trips_to_add)), f"Route {r.route}: existing scheduled trips and the proposed extra departure(s)"))
            show(pd.DataFrame({"": ["departures in the busiest hour", "headway in the busiest hour (min)"], "existing (ACTUAL)": [int(r.departures_in_peak_hour), round(60 / max(r.departures_in_peak_hour, 1))],
                               "proposed (SIMULATED)": [int(r.departures_in_peak_hour + r.trips_to_add), round(60 / (r.departures_in_peak_hour + r.trips_to_add))]}).astype(str))


# ================================================================== 8. METRICS COMPARISON
def page_metrics():
    st.header("Metrics Comparison – current vs simulated network")
    st.warning("The simulated network is a **what-if copy** of the schedule data under stated assumptions (below). **Fewer routes or less distance does not mean a better network:** passenger access, "
               "geographical coverage, travel times and demand were not measured.")
    params = st.session_state.get("opt_params", tuple(mopt.DEFAULTS.values()))
    is_default = params == tuple(mopt.DEFAULTS.values())
    met = mopt.scenario_metrics(params)
    c = st.columns(3)
    scen = c[0].selectbox("Simulated scenario", mopt.SCENARIOS[1:], index=3)
    city = c[1].selectbox("Scope", ["ALL CITIES"] + [x for x in sel_cities if x not in dl.EXCLUDED_FEEDS])
    c[2].markdown(("Thresholds: **Module 6 defaults**." if is_default else "Thresholds: **your what-if values** (set in *Route Optimization*)."))
    cur = met[(met.scenario == "current network") & (met.city == city)].iloc[0]
    sim = met[(met.scenario == scen) & (met.city == city)].iloc[0]
    names = {"routes": "Routes", "scheduled_trips": "Scheduled trips", "est_route_distance_km": "Est. route distance (km)", "avg_route_length_km": "Avg route length (km)",
             "scheduled_trip_km": "Scheduled trip-km", "avg_trips_per_route": "Avg trips per route"}
    cols = st.columns(len(names))
    for col, (k, nme) in zip(cols, names.items()):
        d = sim[k] - cur[k]
        col.metric(nme, f"{sim[k]:,.1f}" if sim[k] % 1 else f"{sim[k]:,.0f}", f"{d:+,.1f} ({100 * d / cur[k]:+.1f}%)" if cur[k] else None, delta_color="off")
    st.caption(f"{KIND['actual']} current values vs {KIND['simulated']} values for the scenario '{scen}'. Deltas are shown neutral on purpose: a change is not automatically good or bad.")
    show(pd.DataFrame({"metric": list(names.values()) + ["Routes longer than 40 km", "Routes with fewer than 2 departures in their busiest hour"],
                       "current network": [cur[k] for k in names] + [cur.routes_over_40km, cur.routes_with_under_2_departures_in_peak_hour],
                       f"simulated: {scen}": [sim[k] for k in names] + [sim.routes_over_40km, sim.routes_with_under_2_departures_in_peak_hour]}).astype(str).replace("nan", "n/a (not defined for this scenario)"))
    chart(viz.compare_bar_fig(cur, sim, list(names), names, f"{scen}: simulated value as % of the current network ({city})"))
    st.subheader("Stop coverage")
    stops = sum(len(dl.load_stops(x)) for x in ([c for c in sel_cities if c not in dl.EXCLUDED_FEEDS] if city == "ALL CITIES" else [city]))
    st.markdown(f"**{stops:,} stops** are served in the current network and in every scenario: merging keeps the absorbed route's unshared stops on the merged route, splitting keeps all stops "
                "(the middle stop is shared), and frequency changes add trips only. Coverage is therefore **preserved by construction**; real accessibility and travel times could not be measured.")
    st.subheader("All scenarios by city")
    t = met[met.city != "ALL CITIES"] if city == "ALL CITIES" else met[met.city == city]
    pick = st.multiselect("Scenarios", mopt.SCENARIOS, default=["current network", scen])
    show(t[t.scenario.isin(pick)][["scenario", "city", "routes", "scheduled_trips", "est_route_distance_km", "avg_route_length_km", "scheduled_trip_km", "avg_trips_per_route"]].sort_values(["city", "scenario"]))
    if is_default:
        saved = dl.load_table("module6_current_vs_simulated_metrics.csv")
        a = met.set_index(["scenario", "city"])[list(names)].astype(float)
        b = saved.set_index(["scenario", "city"])[list(names)].astype(float)
        st.success("Consistency check: these live numbers equal the metrics saved by `run_module6.py`." if np.allclose(a.sort_index().values, b.sort_index().values) else "The live numbers differ from the saved Module 6 table - rerun `python run_module6.py`.")
    with st.expander("Assumptions of the simulation"):
        st.markdown("* **Merge:** the absorbed route's departures are kept; its unshared length (length × (1 − shared-stop share)) is added to the target; the absorbed route disappears.\n"
                    "* **Split:** cut at the middle stop into two routes of half the length, each keeping all departures (trip-km unchanged, trip records double); transfer burden ignored.\n"
                    "* **Frequency:** trips are added until the busiest hour reaches the headway standard; no trips are removed.\n"
                    "* **Combined:** all three, with precedence merge > split > frequency (a route is changed once).\n"
                    "* Metric definitions: scheduled trip-km = Σ trips × route length; route distance = Σ estimated route lengths (straight-line lower bounds for many feeds).")
    with st.expander("What would be needed to judge the real impact"):
        st.markdown("Boardings per route/stop/time period (matched to GTFS ids and dates), vehicle capacity and fleet availability, travel-time and transfer data, the operator's purpose for each route, and validated route shapes.")


# ================================================================== 9. ABOUT
def page_about():
    st.header("About / Project Information")
    st.subheader("Methodology (Modules 1-7)")
    show(pd.DataFrame([
        [1, "Data collection", "Open GTFS bus feeds of 7 cities, inspected read-only; the paid Lepton/Datarade dataset could not be obtained.", "reports/module1_*"],
        [2, "Feature engineering", "Cleaning log, time features, distinct trips/stops, headway, route length (shapes.txt first), stop overlap.", "data/processed/, reports/module2_*"],
        [3, "Exploratory analysis", "Distributions, hourly patterns, route comparison, maps, correlation, outliers investigated not deleted.", "reports/module3_*"],
        [4, "Preprocessing", "Median imputation + indicators, log, standardisation, one-hot, grouped 80:20 split fitted on training only.", "data/processed/module4/"],
        [5, "ML models", "KMeans, DBSCAN (clusters); Random Forest, XGBoost predict the city as a diagnostic.", "models/, reports/module5_*"],
        [6, "Inference & optimisation", "Saved models on unseen routes; evidence-based candidates; merge/split/frequency scenarios on a copy.", "data/inference/, data/simulated/"],
        [7, "Dashboard", "This Streamlit application (modules/ + app.py).", "app.py"]], columns=["Module", "Step", "What was done", "Where"]))
    st.subheader("Architecture")
    st.code("run_module1-6.py  ->  data/processed, models/, data/inference, data/simulated, reports/\n"
            "modules/data_loader.py      cached loading of those files\n"
            "modules/data_validation.py  quality checks, upload validation\n"
            "modules/route_analysis.py   route profiles, filters, peer comparison\n"
            "modules/clustering.py       KMeans / DBSCAN results, PCA projection\n"
            "modules/predictions.py      Random Forest / XGBoost live predictions and evaluation\n"
            "modules/optimization.py     what-if candidates and scenario metrics (uses src/optimization.py)\n"
            "modules/visualizations.py   Plotly figures\n"
            "app.py                      navigation and the nine sections", language="text")
    st.subheader("Technologies")
    st.markdown(f"Python {platform.python_version()}, pandas, NumPy, scikit-learn (KMeans, DBSCAN, Random Forest, PCA), XGBoost, Plotly, Streamlit, Matplotlib/Seaborn/Folium (reports).")
    st.subheader("Important limitations")
    st.markdown("* GTFS holds **scheduled** service only - no ridership, occupancy, capacity or delays. Nothing here is a passenger or demand figure.\n"
                "* Only 7 of the 23 planned cities (Lepton/Datarade is a paid dataset); several feeds are community-made or old (Delhi, Kochi calendars 2022-24).\n"
                "* Feeds are not directly comparable: Hyderabad's trips look like whole vehicle duties; Delhi, Kochi and Pune show near-constant scheduled speeds.\n"
                "* Clusters are weakly separated and are not performance classes; DBSCAN noise is not an error.\n"
                "* The classifiers predict the **city**, not route quality.\n"
                "* Optimisation suggestions are candidates; simulated results use stated assumptions and are not validated forecasts.")
    st.subheader("How the data is labelled")
    for v in KIND.values():
        st.markdown(f"* {v}")
    st.caption(f"Streamlit {st.__version__} · pandas {pd.__version__}")


PAGES = dict(zip(SECTIONS, [page_home, page_dataset, page_eda, page_routes, page_clusters, page_predictions, page_optimization, page_metrics, page_about]))
PAGES[section]()
