"""Module 2 / step 2 - feature engineering from SCHEDULE data only.

GTFS has no passenger counts. Nothing here estimates ridership: 'trips', 'stop visits' and 'headway' describe
the PLANNED service. A route with few scheduled trips is not automatically inefficient.
"""
import numpy as np
import pandas as pd

from .gtfs_utils import haversine, route_geometry, stop_overlap

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
PERIODS = ["morning", "afternoon", "evening", "night"]
PERIOD_RULES = {"morning": "05:00-11:59", "afternoon": "12:00-16:59", "evening": "17:00-20:59", "night": "21:00-04:59"}


def period_of(hour):
    h = pd.Series(hour).reset_index(drop=True)
    return np.select([h.between(5, 11), h.between(12, 16), h.between(17, 20)], PERIODS[:3], default="night")


def service_flags(clean):
    """Per service_id: which weekdays it runs (from calendar.txt). None if the feed has no calendar.txt."""
    cal = clean.get("calendar")
    if cal is None:
        return None
    out = pd.DataFrame({"service_id": cal.service_id})
    for d in DAYS:
        out[f"runs_{d}"] = (pd.to_numeric(cal[d], errors="coerce").fillna(0) == 1).values if d in cal else False
    out["service_day_type"] = np.select(
        [out[[f"runs_{d}" for d in DAYS[:5]]].any(axis=1) & out[["runs_saturday", "runs_sunday"]].any(axis=1),
         out[[f"runs_{d}" for d in DAYS[:5]]].any(axis=1), out[["runs_saturday", "runs_sunday"]].any(axis=1)],
        ["weekday_and_weekend", "weekday_only", "weekend_only"], default="no_day")
    return out


def trip_features(clean):
    st, t = clean["stop_times"], clean["trips"]
    g = st.groupby("trip_id", sort=False).agg(start_s=("dep_s", "first"), end_s=("arr_s", "last"),
                                              n_stops=("stop_id", "size")).reset_index()
    keep = [c for c in ["trip_id", "route_id", "service_id", "direction_id", "shape_id"] if c in t.columns]
    tf = t[keep].merge(g, on="trip_id")
    tf["start_hour"] = ((tf.start_s // 3600) % 24).astype(int)            # GTFS 25:10:00 -> clock hour 1
    tf["start_minute"] = ((tf.start_s % 3600) // 60).astype(int)
    tf["departure_clock"] = tf.start_hour.astype(str).str.zfill(2) + ":" + tf.start_minute.astype(str).str.zfill(2)
    tf["period"] = period_of(tf.start_hour)
    tf["starts_after_midnight"] = tf.start_s >= 86400                      # written as >= 24:00:00 in the feed
    tf["duration_min"] = (tf.end_s - tf.start_s) / 60
    tf["from_frequency"] = tf.trip_id.astype(str).str.contains("__f", regex=False)
    tf["time_backwards"] = tf.trip_id.isin(clean["time_backwards_trips"])
    sf = service_flags(clean)
    if sf is not None:
        tf = tf.merge(sf, on="service_id", how="left")
        flag_cols = [f"runs_{d}" for d in DAYS]
        tf["service_in_calendar"] = tf.service_day_type.notna()
        tf[flag_cols] = tf[flag_cols].fillna(False).astype(bool)
        tf["service_day_type"] = tf.service_day_type.fillna("unknown")
    return tf


def _gaps(tf):
    """Gap in minutes between consecutive scheduled departures of the same route_id AND service_id."""
    x = tf.sort_values(["route_id", "service_id", "start_s"]).copy()
    x["gap_min"] = x.groupby(["route_id", "service_id"]).start_s.diff() / 60
    return x[x.gap_min > 0]       # 0 = simultaneous departures (e.g. two variants under one route_id): headway undefined


def route_hour_table(clean, tf):
    """Route x clock-hour table. trips_* = distinct trips whose first departure is in that hour."""
    trips = tf.groupby(["route_id", "start_hour"]).size().rename("trips_all")
    parts = [trips]
    if "runs_wednesday" in tf:
        parts.append(tf[tf.runs_wednesday].groupby(["route_id", "start_hour"]).size().rename("trips_typical_weekday"))
        parts.append(tf[tf.runs_sunday].groupby(["route_id", "start_hour"]).size().rename("trips_typical_sunday"))
    gp = _gaps(tf)
    parts.append(gp.groupby(["route_id", "start_hour"]).gap_min.median().rename("median_headway_min"))
    rh = pd.concat(parts, axis=1)
    rh.index.names = ["route_id", "hour"]
    rh = rh.reset_index()
    for c in ("trips_typical_weekday", "trips_typical_sunday"):
        if c in rh:      # trips exist in the hour for this route, so "none on that day" is a real 0, not a missing value
            rh[c] = rh[c].fillna(0).astype(int)
    st = clean["stop_times"][["trip_id", "arr_s"]].merge(tf[["trip_id", "route_id"]], on="trip_id")
    st["hour"] = ((st.arr_s // 3600) % 24).astype(int)
    v = st.groupby(["route_id", "hour"]).size().rename("scheduled_stop_visits").reset_index()
    rh = rh.merge(v, on=["route_id", "hour"], how="outer")
    rh["trips_all"] = rh.trips_all.fillna(0).astype(int)   # a stop call in an hour with no trip STARTING is a real 0 trips started
    rh["period"] = period_of(rh.hour)
    return rh


def stop_usage_table(clean, tf):
    """Scheduled stop visits per stop (how often buses are timetabled to call) - NOT passenger boardings."""
    st = clean["stop_times"][["trip_id", "stop_id", "arr_s"]].merge(tf[["trip_id", "route_id"]], on="trip_id")
    st["hour"] = ((st.arr_s // 3600) % 24).astype(int)
    per_hour = st.groupby(["stop_id", "hour"]).size().rename("visits").reset_index()
    tot = per_hour.groupby("stop_id").visits.sum().rename("scheduled_visits")
    pk = per_hour.loc[per_hour.groupby("stop_id").visits.idxmax()].set_index("stop_id")[["hour", "visits"]]
    pk.columns = ["peak_hour", "peak_hour_visits"]
    pairs = st.drop_duplicates(["stop_id", "route_id"])[["stop_id", "route_id"]]
    n_routes = pairs.groupby("stop_id").size().rename("n_routes")
    su = pd.concat([tot, pk, n_routes], axis=1).reset_index()
    su = su.merge(clean["stops"][["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id", how="left")
    return su, n_routes, pairs


def shape_lengths_km(shapes, wanted_ids):
    sh = shapes[shapes.shape_id.isin(wanted_ids)].copy()
    sh["lat"] = pd.to_numeric(sh.shape_pt_lat, errors="coerce"); sh["lon"] = pd.to_numeric(sh.shape_pt_lon, errors="coerce")
    sh["seq"] = pd.to_numeric(sh.shape_pt_sequence, errors="coerce")
    sh = sh.dropna(subset=["lat", "lon", "seq"]).sort_values(["shape_id", "seq"])
    seg = haversine(sh.lat.shift(), sh.lon.shift(), sh.lat, sh.lon)
    seg[sh.shape_id != sh.shape_id.shift()] = 0
    return seg.groupby(sh.shape_id).sum()


def route_features(clean, tf, shapes, n_routes_at_stop, pairs):
    r, s = clean["routes"], clean["stops"]
    g = tf.groupby("route_id")
    rf = g.agg(n_trips=("trip_id", "nunique"), median_stops_per_trip=("n_stops", "median"),
               avg_trip_duration_min=("duration_min", "mean"), median_trip_duration_min=("duration_min", "median"),
               n_service_ids=("service_id", "nunique"), trips_from_frequency=("from_frequency", "sum"),
               has_time_backwards_trip=("time_backwards", "any"), first_departure_h=("start_s", lambda x: x.min() / 3600),
               last_departure_h=("start_s", lambda x: x.max() / 3600))
    if "direction_id" in tf.columns:
        rf["n_directions"] = g.direction_id.nunique()
    rf["service_span_h"] = rf.last_departure_h - rf.first_departure_h
    hr = tf.groupby(["route_id", "start_hour"]).size().rename("n").reset_index()
    rf["n_active_hours"] = hr.groupby("route_id").size()
    top = hr.loc[hr.groupby("route_id").n.idxmax()].set_index("route_id")
    rf["peak_hour"], rf["peak_hour_trips"] = top.start_hour, top.n
    rf["trips_per_active_hour"] = rf.n_trips / rf.n_active_hours
    per = pd.crosstab(tf.route_id, tf.period)
    for p in PERIODS:
        rf[f"trips_{p}"] = per[p] if p in per else 0
    rf["median_headway_min"] = _gaps(tf).groupby("route_id").gap_min.median()
    if "runs_monday" in tf.columns:
        for d in DAYS:
            rf[f"trips_{d}"] = tf.groupby("route_id")[f"runs_{d}"].sum()
        rf["avg_trips_per_weekday"] = rf[[f"trips_{d}" for d in DAYS[:5]]].mean(axis=1)
        rf["avg_trips_per_weekend_day"] = rf[["trips_saturday", "trips_sunday"]].mean(axis=1)
        rf["weekend_to_weekday_ratio"] = rf.avg_trips_per_weekend_day / rf.avg_trips_per_weekday.replace(0, np.nan)
    # ---- route length: shapes.txt first (mentor rule), stop coordinates as fallback
    length_stops, sbr, ends = route_geometry(dict(stop_times=clean["stop_times"], trips=clean["trips"], stops=s))
    rf["length_km_stops"] = length_stops
    rf["length_km_shape"] = np.nan
    if shapes is not None and "shape_id" in tf.columns:
        sl = shape_lengths_km(shapes, set(tf.shape_id.dropna()))
        rs = tf[["route_id", "shape_id"]].dropna().drop_duplicates()
        rs["len"] = rs.shape_id.map(sl)
        rf["length_km_shape"] = rs.groupby("route_id")["len"].max()          # longest scheduled variant
    ratio = rf.length_km_shape / rf.length_km_stops.replace(0, np.nan)
    use_shape = rf.length_km_shape.notna() & ratio.between(0.5, 3)           # sanity rule, documented in the feature dictionary
    rf["length_km"] = np.where(use_shape, rf.length_km_shape, rf.length_km_stops)
    rf["length_method"] = np.where(use_shape, "shapes.txt", np.where(rf.length_km_shape.notna(), "stop coordinates (shape failed sanity check)",
                                                                       "stop coordinates (straight-line, approximate)"))
    rf["n_unique_stops"] = pd.Series({k: len(v) for k, v in sbr.items()})
    rf["stops_per_km"] = rf.n_unique_stops / rf.length_km.clip(lower=0.5)
    rf["avg_speed_kmh"] = rf.length_km / (rf.median_trip_duration_min / 60).clip(lower=0.05)
    rf["speed_implausible"] = (rf.avg_speed_kmh > 80) | (rf.avg_speed_kmh < 3)
    # ---- stop sharing
    names = r.set_index("route_id").route_name.to_dict()
    ov = stop_overlap(sbr, names, ends)
    ov["overlap_partner_name"] = ov.overlap_partner.map(names)
    rf = rf.join(ov.rename(columns={"overlap_jaccard": "max_stop_overlap", "overlap_share": "overlap_share_of_route"}))
    pr = pairs.assign(n=pairs.stop_id.map(n_routes_at_stop))
    rf["mean_routes_per_stop"] = pr.groupby("route_id").n.mean()
    rf["sparse_schedule"] = rf.n_trips < 3          # descriptive flag only - NOT a verdict of inefficiency
    rf = rf.join(r.set_index("route_id")[["route_name"] + (["route_type"] if "route_type" in r else [])])
    rf = rf.reset_index().rename(columns={"index": "route_id"})
    first = ["route_id", "route_name"] + (["route_type"] if "route_type" in rf else [])
    return rf[first + [c for c in rf.columns if c not in first]]


def build_all(clean, shapes=None):
    tf = trip_features(clean)
    rh = route_hour_table(clean, tf)
    su, n_routes, pairs = stop_usage_table(clean, tf)
    rf = route_features(clean, tf, shapes, n_routes, pairs)
    return dict(trip_features=tf, route_hour_features=rh, stop_usage=su, route_features=rf)
