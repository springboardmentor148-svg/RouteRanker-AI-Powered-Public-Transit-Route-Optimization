"""Plotly figure builders. Titles state what is shown (scheduled supply, model output, simulation) so charts are not misread as passenger data."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PERIOD_ORDER = ["morning", "afternoon", "evening", "night"]
PERIOD_COLORS = {"morning": "#f4a261", "afternoon": "#e9c46a", "evening": "#2a9d8f", "night": "#264653"}
LABELS = {"n_trips": "scheduled trips per route", "n_unique_stops": "distinct stops per route", "length_km": "estimated route length (km)",
          "service_span_h": "scheduled service span (h)", "median_headway_min": "median headway (min)", "avg_speed_kmh": "scheduled speed (km/h)",
          "max_stop_overlap": "max stop overlap with another route", "trips_per_active_hour": "scheduled trips per active hour"}


def _lay(fig, title, h=380):
    fig.update_layout(title=title, height=h, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def hist_fig(df, col, color=None, log_x=False, nbins=40, title=None):
    d = df[df[col].notna()]
    fig = px.histogram(d, x=col, color=color, nbins=nbins, log_x=log_x, labels={col: LABELS.get(col, col)}, barmode="overlay" if color else "relative", opacity=.8)
    fig.update_yaxes(title="number of routes")
    return _lay(fig, title or f"Distribution of {LABELS.get(col, col)}")


def hourly_fig(h, cols, title):
    """h: DataFrame with 'hour' and the given trip columns (scheduled trips starting in each clock hour)."""
    fig = go.Figure()
    for c, name in cols.items():
        fig.add_bar(x=h.hour, y=h[c], name=name)
    fig.update_layout(barmode="group", xaxis=dict(dtick=1, title="clock hour of first departure"), yaxis_title="distinct scheduled trips")
    return _lay(fig, title)


def period_fig(p, title):
    fig = px.bar(p, x="period", y="scheduled_trips", color="period", color_discrete_map=PERIOD_COLORS, text=p["share_%"].astype(str) + "%", category_orders={"period": PERIOD_ORDER})
    fig.update_layout(showlegend=False, yaxis_title="distinct scheduled trips")
    return _lay(fig, title, 340)


def box_fig(df, y, by="city", log_y=True):
    fig = px.box(df[df[y].notna()], x=by, y=y, log_y=log_y, points=False, labels={y: LABELS.get(y, y)})
    return _lay(fig, f"{LABELS.get(y, y)} by city (box = middle 50% of routes)")


def corr_fig(df, cols):
    c = df[[x for x in cols if x in df]].corr(method="spearman").round(2)
    fig = px.imshow(c, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
    return _lay(fig, "Spearman correlation of route features (association, not causation)", 520)


def top_routes_fig(df, n=15, by="n_trips"):
    t = df.nlargest(n, by).iloc[::-1]
    fig = px.bar(t, x=by, y=t.route_name.astype(str) + " (" + t.city + ")", orientation="h", labels={by: LABELS.get(by, by), "y": "route"})
    return _lay(fig, f"Routes with the most {LABELS.get(by, by)} (scheduled service - not crowding)", 460)


def scatter_fig(df, x, y, color=None, log_y=False, hover=("route_name", "city")):
    d = df[list(dict.fromkeys([x, y] + ([color] if color else []) + [h for h in hover if h in df]))].dropna(subset=[x, y])
    rho = d[[x, y]].corr(method="spearman").iloc[0, 1]
    fig = px.scatter(d, x=x, y=y, color=color, log_y=log_y, hover_data=[h for h in hover if h in d], opacity=.55, labels={x: LABELS.get(x, x), y: LABELS.get(y, y)})
    return _lay(fig, f"{LABELS.get(y, y)} vs {LABELS.get(x, x)}  (Spearman rho = {rho:.2f})", 420)


def stops_map_fig(stops, city, max_points=8000):
    s = stops.dropna(subset=["stop_lat", "stop_lon"])
    s = s.sample(min(len(s), max_points), random_state=0)
    fig = go.Figure(go.Scattermap(lat=s.stop_lat, lon=s.stop_lon, mode="markers", text=s.stop_name + ": " + s.n_routes.astype(str) + " routes call here",
                                  marker=dict(size=np.clip(s.n_routes, 3, 14), color=np.log1p(s.n_routes), colorscale="YlOrRd", opacity=.7, colorbar=dict(title="log(1+routes)"))))
    fig.update_layout(map=dict(style="open-street-map", center=dict(lat=s.stop_lat.median(), lon=s.stop_lon.median()), zoom=9.5), margin=dict(l=0, r=0, t=40, b=0), height=520,
                      title=f"{city.title()}: stop locations coloured by the number of routes calling there (scheduled service)")
    return fig


def pca_fig(emb, color, title):
    d = emb.sample(min(len(emb), 6000), random_state=0)
    fig = px.scatter(d, x="pc1", y="pc2", color=color, opacity=.6, hover_data=["city", "route_name", "n_trips", "n_unique_stops", "length_km"], labels={"pc1": "PCA 1", "pc2": "PCA 2"})
    fig.update_traces(marker=dict(size=5))
    return _lay(fig, title, 520)


def share_bar_fig(emb, group, by="city", title=""):
    t = pd.crosstab(emb[group], emb[by], normalize="index").reset_index().melt(id_vars=group, var_name=by, value_name="share")
    fig = px.bar(t, x=group, y="share", color=by, labels={group: group.replace("_", " ")})
    return _lay(fig, title, 380)


def profile_heatmap(z, title):
    fig = px.imshow(z, text_auto=".1f", color_continuous_scale="RdBu_r", zmin=-2.5, zmax=2.5, aspect="auto", labels=dict(x="feature", y="cluster", color="z-score"))
    return _lay(fig, title, 420)


def confusion_fig(cm, classes, title):
    fig = px.imshow(cm, x=classes, y=classes, text_auto=True, color_continuous_scale="Blues", labels=dict(x="predicted city", y="actual city"))
    return _lay(fig, title, 440)


def proba_fig(p, classes, title):
    t = p.melt(id_vars=["model"], value_vars=classes, var_name="city", value_name="probability")
    fig = px.bar(t, x="city", y="probability", color="model", barmode="group", range_y=[0, 1])
    return _lay(fig, title, 340)


def compare_bar_fig(cur, scen, cols, names, title):
    """Current network = 100%; the simulated value is shown relative to it (a change is not automatically an improvement)."""
    rows = []
    for c in cols:
        rows.append(dict(metric=names.get(c, c), network="current", pct=100.0))
        rows.append(dict(metric=names.get(c, c), network="simulated", pct=100 * scen[c] / cur[c] if cur[c] else np.nan))
    fig = px.bar(pd.DataFrame(rows), x="metric", y="pct", color="network", barmode="group", color_discrete_map={"current": "#2a9d8f", "simulated": "#e76f51"},
                 labels={"pct": "% of the current network"})
    fig.add_hline(y=100, line_dash="dash", line_color="grey")
    return _lay(fig, title, 380)


def route_hours_fig(h, proposed=None, title=""):
    fig = go.Figure(go.Bar(x=h.hour, y=h.trips_all, name="scheduled trips (actual)", marker_color="#457b9d"))
    if proposed:
        hr, add = proposed
        fig.add_bar(x=[hr], y=[add], name="proposed extra departure(s) (SIMULATED)", marker_color="#e76f51")
    fig.update_layout(barmode="stack", xaxis=dict(dtick=1, title="clock hour of first departure"), yaxis_title="scheduled trips")
    return _lay(fig, title, 330)
