"""Route-level analysis helpers (Module 3 / 2 features)."""
import numpy as np
import pandas as pd

from src import eda


def filter_routes(df, cities=None, trips=None, length=None, query=""):
    d = df
    if cities is not None:
        d = d[d.city.isin(cities)]
    if trips is not None:
        d = d[d.n_trips.between(*trips)]
    if length is not None:
        d = d[d.length_km.between(*length) | d.length_km.isna()]
    if query:
        d = d[d.route_name.astype(str).str.contains(query, case=False, regex=False)]
    return d


def route_label(r):
    return f"{r.route_name}  (id {r.route_id})"


def peer_percentiles(df, city, route_id, cols=("n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min")):
    """Where a route stands among routes of its own city (percentile, 0-100). Descriptive only."""
    g = df[df.city == city]
    r = g[g.route_id == route_id].iloc[0]
    out = []
    for c in cols:
        if c in g and pd.notna(r[c]):
            out.append(dict(feature=c, value=round(float(r[c]), 2), city_median=round(float(g[c].median()), 2), percentile_in_city=round(float((g[c].dropna() <= r[c]).mean() * 100), 0)))
    return pd.DataFrame(out)


def group_comparison(df):
    """Routes grouped by scheduled trips (lowest quarter / middle / highest quarter): median of the other features."""
    return eda.group_comparison(df).reset_index()


def top_routes(df, n=15, by="n_trips", ascending=False):
    return df.sort_values(by, ascending=ascending).head(n)


def hourly_for_route(hours, city, route_id):
    h = hours[(hours.city == city) & (hours.route_id == route_id)].sort_values("hour")
    full = pd.DataFrame({"hour": range(24)}).merge(h[["hour", "trips_all"]], on="hour", how="left").fillna({"trips_all": 0})
    return full
