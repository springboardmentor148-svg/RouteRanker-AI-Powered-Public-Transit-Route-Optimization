"""RouteRanker – Streamlit dashboard.  Run:  streamlit run app.py"""
import glob, os, tempfile
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import pipeline
from src.features import BUS_CAPACITY
from src.synthetic import make_synthetic_gtfs

st.set_page_config(page_title="RouteRanker", page_icon="🚌", layout="wide")
_k = [0]
def nk():
    _k[0] += 1
    return f"chart{_k[0]}"


COLORS = {"Overcrowded": "#d62728", "Balanced": "#2ca02c", "Underutilized": "#ff7f0e"}

st.title("🚌 RouteRanker – AI-Powered Public Transit Route Optimization")
st.caption("GTFS → features → clustering & classification → merge / split / frequency recommendations")

# ---------------- sidebar: data source ----------------
with st.sidebar:
    st.header("1 · Data")
    local = sorted(p for p in glob.glob("data/raw/*/*.zip") + [d for d in glob.glob("data/raw/*") if os.path.isfile(os.path.join(d, "stop_times.txt"))]
                   if "sample_city" not in p)
    mode = st.radio("Source", ["Demo (synthetic city)", "Local feed (data/raw)", "Upload GTFS .zip"])
    src, city = None, "Demo"
    if mode.startswith("Demo"):
        src = make_synthetic_gtfs("data/raw/sample_city") if not os.path.exists("data/raw/sample_city/stop_times.txt") else "data/raw/sample_city"
    elif mode.startswith("Local"):
        if local:
            pick = st.selectbox("Feed", local)
            src, city = pick, os.path.basename(os.path.dirname(pick) if pick.endswith(".zip") else pick)
        else:
            st.warning("No feeds in data/raw/. Run `python download_data.py` first.")
    else:
        up = st.file_uploader("GTFS zip (routes, trips, stop_times, stops, calendar)", type="zip")
        if up:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip"); tmp.write(up.getbuffer()); tmp.close()
            src, city = tmp.name, up.name.replace(".zip", "")
    st.header("2 · Assumptions")
    cap = st.slider("Bus capacity (seated + standing)", 40, 120, BUS_CAPACITY, 5)
    hi = st.slider("Target load – overcrowded routes", 0.6, 1.0, 0.85, 0.05)
    lo = st.slider("Target load – underutilized routes", 0.4, 0.9, 0.70, 0.05)
    mo = st.slider("Merge if stop overlap ≥", 0.3, 0.9, 0.50, 0.05)

if src is None:
    st.info("Choose or upload a GTFS feed in the sidebar."); st.stop()


@st.cache_data(show_spinner="Running pipeline (clean → features → models → simulation)…")
def run(src, city, cap, hi, lo, mo):
    return pipeline.run(src, capacity=cap, city=city, target_hi=hi, target_lo=lo, merge_overlap=mo)


try:
    R = run(src, city, cap, hi, lo, mo)
except Exception as e:
    st.error(f"Could not process this feed: {e}"); st.stop()
rf, hourly, rec, kp, clf = R["routes"], R["hourly"], R["rec"], R["kpis"], R["clf"]

st.info("ℹ️ GTFS contains schedules, not passenger counts. Ridership here is an **estimated relative demand index** "
        "built from stop connectivity + a typical hourly profile. Plug in AFC/ticketing data for absolute numbers.", icon="ℹ️")

c = st.columns(5)
c[0].metric("Routes", len(rf)); c[1].metric("Stops", len(R["feed"]["stops"]))
c[2].metric("Overcrowded", int((rec.predicted_performance == "Overcrowded").sum()))
c[3].metric("Underutilized", int((rec.predicted_performance == "Underutilized").sum()))
c[4].metric("Model F1 (best)", f"{clf['metrics'].f1_macro.max():.2f}", clf["best"])

t1, t2, t3, t4, t5, t6, t7 = st.tabs(["📊 EDA", "🧩 Clusters", "🤖 Model", "💡 Recommendations", "🔬 Scenario", "🗺️ Route map", "🌆 All cities"])

# ---------------- EDA ----------------
with t1:
    a, b = st.columns(2)
    hr = hourly.groupby("hour").agg(passengers=("passengers", "sum"), trips=("trips", "sum")).reset_index()
    fig = go.Figure()
    fig.add_bar(x=hr.hour, y=hr.trips, name="Trips", marker_color="#bbb", yaxis="y2", opacity=.6)
    fig.add_scatter(x=hr.hour, y=hr.passengers, name="Est. passengers", line=dict(color="#d62728", width=3))
    fig.update_layout(title="Hourly ridership curve (estimated) vs supply", yaxis2=dict(overlaying="y", side="right", title="Trips"),
                      yaxis_title="Passengers", xaxis_title="Hour of day", legend=dict(orientation="h"))
    a.plotly_chart(key=nk(), figure_or_data=fig, width="stretch")
    top = rf.nlargest(20, "total_passengers")
    b.plotly_chart(key=nk(), figure_or_data=px.bar(top, x="route_name", y="total_passengers", color="performance", color_discrete_map=COLORS,
                          title="Top 20 routes by estimated daily passengers"), width="stretch")
    heat = hourly.pivot_table(index="route_id", columns="hour", values="load_factor", aggfunc="mean")
    heat = heat.loc[rf.set_index("route_id").loc[heat.index].peak_load_factor.sort_values(ascending=False).index[:40]]
    st.plotly_chart(key=nk(), figure_or_data=px.imshow(heat, aspect="auto", color_continuous_scale="RdYlGn_r", zmin=0, zmax=1.5,
                              title="Load factor heatmap — 40 busiest routes × hour"), width="stretch")
    a, b = st.columns(2)
    sd = R["stops"]
    mfig = go.Figure(go.Densitymap(lat=sd.stop_lat, lon=sd.stop_lon, z=sd.n_routes, radius=14, colorscale="YlOrRd"))
    mfig.update_layout(map=dict(style="open-street-map", center=dict(lat=sd.stop_lat.mean(), lon=sd.stop_lon.mean()), zoom=10),
                       margin=dict(l=0, r=0, t=30, b=0), title="Route density heatmap (routes per stop)", height=420)
    a.plotly_chart(key=nk(), figure_or_data=mfig, width="stretch")
    b.plotly_chart(key=nk(), figure_or_data=px.scatter(rf, x="length_km", y="avg_headway_min", color="performance", color_discrete_map=COLORS,
                              size="n_trips", hover_name="route_name", title="Route length vs headway"), width="stretch")
    st.subheader("Overlapping routes (stop overlap ≥ 50%)")
    ov = rf[rf.overlap_jaccard >= .5][["route_name", "overlap_partner", "overlap_jaccard", "performance"]].sort_values("overlap_jaccard", ascending=False)
    st.dataframe(ov, width="stretch", hide_index=True)
    with st.expander("Data cleaning report"):
        st.json({k: int(v) for k, v in R["report"].items()})

# ---------------- Clusters ----------------
with t2:
    cl = R["clusters"].merge(rf[["route_id", "route_name", "performance", "n_trips", "length_km"]], on="route_id")
    ci = R["cluster_info"]
    st.write(f"**KMeans**: best k = {ci['best_k']} (silhouette {max(ci['silhouettes'].values()):.2f}) · "
             f"**DBSCAN**: {ci['dbscan_clusters']} clusters, {ci['dbscan_noise']} noise/anomalous routes · PCA explains {ci['var_explained']:.0%}")
    a, b = st.columns(2)
    cl["kmeans_cluster"] = cl.kmeans_cluster.astype(str); cl["dbscan_cluster"] = cl.dbscan_cluster.astype(str)
    a.plotly_chart(key=nk(), figure_or_data=px.scatter(cl, x="pc1", y="pc2", color="kmeans_cluster", hover_name="route_name", title="KMeans route clusters (PCA)"), width="stretch")
    b.plotly_chart(key=nk(), figure_or_data=px.scatter(cl, x="pc1", y="pc2", color="dbscan_cluster", hover_name="route_name", title="DBSCAN (-1 = anomalous routes)"), width="stretch")
    st.subheader("KMeans cluster profiles"); st.dataframe(ci["cluster_profile"], width="stretch")
    st.plotly_chart(key=nk(), figure_or_data=px.line(pd.Series(ci["silhouettes"]).rename("silhouette").reset_index(), x="index", y="silhouette", markers=True,
                            title="Silhouette vs k", labels={"index": "k"}), width="stretch")

# ---------------- Model ----------------
with t3:
    st.write(f"Train: {clf['n_train']} routes · Validation: {clf['n_val']} routes · "
             f"3-fold CV macro-F1 (RF): {clf['cv_f1']:.2f}" if not np.isnan(clf["cv_f1"]) else f"Train {clf['n_train']} / Val {clf['n_val']}")
    a, b = st.columns(2)
    a.subheader("Validation metrics"); a.dataframe(clf["metrics"].style.format("{:.3f}").highlight_max(axis=0), width="stretch")
    a.success(f"Selected model: **{clf['best']}**")
    b.subheader("Confusion matrix (validation)")
    b.plotly_chart(key=nk(), figure_or_data=px.imshow(clf["confusion"], text_auto=True, color_continuous_scale="Blues"), width="stretch")
    st.plotly_chart(key=nk(), figure_or_data=px.bar(clf["importance"].head(10).iloc[::-1], orientation="h", title="Top feature importances"), width="stretch")
    st.caption("Labels derive from the estimated load factor; those demand columns are excluded from model inputs to prevent leakage.")

# ---------------- Recommendations ----------------
with t4:
    f1, f2 = st.columns(2)
    acts = f1.multiselect("Action", sorted(rec.action.unique()), default=[a for a in rec.action.unique() if a != "No change"])
    q = f2.text_input("Search route")
    v = rec[rec.action.isin(acts)]
    if q: v = v[v.route_name.str.contains(q, case=False, na=False)]
    show = v[["route_name", "predicted_performance", "confidence", "action", "recommendation", "trip_change", "merge_into",
              "peak_load_factor", "mean_load_factor", "n_trips", "length_km"]].sort_values("peak_load_factor", ascending=False)
    st.dataframe(show, width="stretch", hide_index=True, column_config={
        "confidence": st.column_config.ProgressColumn("confidence", min_value=0, max_value=1, format="%.2f"),
        "peak_load_factor": st.column_config.NumberColumn(format="%.2f"), "mean_load_factor": st.column_config.NumberColumn(format="%.2f"),
        "length_km": st.column_config.NumberColumn(format="%.1f")})
    st.download_button("⬇️ Download recommendations (CSV)", rec.drop(columns=["demand_base"]).to_csv(index=False), "recommendations.csv")
    st.plotly_chart(key=nk(), figure_or_data=px.pie(rec, names="action", title="Recommended actions", hole=.45), width="stretch")

# ---------------- Scenario ----------------
with t5:
    st.subheader("Current vs optimized")
    k2 = kp.copy(); k2["Change"] = k2.Optimized - k2.Current
    st.dataframe(k2.style.format({"Current": "{:,.2f}", "Optimized": "{:,.2f}", "Change": "{:+,.2f}"}), width="stretch", hide_index=True)
    sim = R["sim"]
    a, b = st.columns(2)
    cur = hourly.groupby("hour").agg(t=("trips", "sum"), p=("passengers", "sum"))
    new = sim.groupby("hour").agg(t=("new_trips", "sum"), p=("new_pass", "sum"))
    fig = go.Figure()
    fig.add_bar(x=cur.index, y=cur.t, name="Current trips"); fig.add_bar(x=new.index, y=new.t, name="Optimized trips")
    fig.update_layout(barmode="group", title="Trips by hour")
    a.plotly_chart(key=nk(), figure_or_data=fig, width="stretch")
    lf = go.Figure()
    lf.add_scatter(x=cur.index, y=cur.p / (cur.t * cap), name="Current", line=dict(width=3))
    lf.add_scatter(x=new.index, y=new.p / (new.t * cap).replace(0, np.nan), name="Optimized", line=dict(width=3))
    lf.add_hline(y=1, line_dash="dash", line_color="red"); lf.update_layout(title="System load factor by hour", yaxis_title="Load factor")
    b.plotly_chart(key=nk(), figure_or_data=lf, width="stretch")
    rid = st.selectbox("Inspect a route", rec.sort_values("peak_load_factor", ascending=False).route_id,
                       format_func=lambda x: rec.set_index("route_id").route_name[x])
    s1 = sim[sim.route_id == rid].sort_values("hour")
    rf1 = go.Figure()
    rf1.add_bar(x=s1.hour, y=s1.trips, name="Current trips"); rf1.add_bar(x=s1.hour, y=s1.new_trips, name="Optimized trips")
    rf1.add_scatter(x=s1.hour, y=s1.load_factor, name="Current LF", yaxis="y2"); rf1.add_scatter(x=s1.hour, y=s1.new_lf, name="Optimized LF", yaxis="y2")
    rf1.update_layout(barmode="group", yaxis2=dict(overlaying="y", side="right", title="Load factor"), title=rec.set_index("route_id").recommendation[rid])
    st.plotly_chart(key=nk(), figure_or_data=rf1, width="stretch")

# ---------------- Map ----------------
with t6:
    sel = st.selectbox("Route", rec.route_id, format_func=lambda x: f"{rec.set_index('route_id').route_name[x]} · {rec.set_index('route_id').action[x]}", key="mapsel")
    f = R["feed"]
    tid = f["trips"][f["trips"].route_id == sel].trip_id
    stt = f["stop_times"][f["stop_times"].trip_id.isin(tid)]
    best = stt.groupby("trip_id").size().idxmax()
    line = stt[stt.trip_id == best].sort_values("stop_sequence").merge(f["stops"], on="stop_id")
    m = go.Figure(go.Scattermap(lat=line.stop_lat, lon=line.stop_lon, mode="lines+markers", text=line.stop_name,
                                marker=dict(size=7), line=dict(width=3, color="#d62728")))
    m.update_layout(map=dict(style="open-street-map", center=dict(lat=line.stop_lat.mean(), lon=line.stop_lon.mean()), zoom=11),
                    margin=dict(l=0, r=0, t=0, b=0), height=520)
    st.plotly_chart(key=nk(), figure_or_data=m, width="stretch")
    st.write(rec.set_index("route_id").recommendation[sel])

# ---------------- All cities ----------------
with t7:
    f = "outputs/all_cities_summary.csv"
    if os.path.exists(f):
        cs = pd.read_csv(f)
        st.dataframe(cs, width="stretch", hide_index=True)
        m = cs.melt(id_vars="city", value_vars=["overcrowded", "overcrowded_after", "underutilized", "underutilized_after"])
        st.plotly_chart(key=nk(), figure_or_data=px.bar(m, x="city", y="value", color="variable", barmode="group",
                        title="Problem routes per city: current vs optimized"), width="stretch")
    else:
        st.info("Run `python -m src.pipeline --all` to build the cross-city summary (reads every feed in data/raw/).")
