"""Module 2 / step 1 - documented cleaning of raw GTFS.

Raw files are never modified: cleaning builds NEW tables. Every removal / fill / flag is written to a
cleaning log (rows before/after + reason), because records must not be dropped or replaced
without a documented justification. Missing values are NEVER silently replaced by zero.
"""
import numpy as np
import pandas as pd

from . import inspect_gtfs as ig
from .gtfs_utils import expand_frequencies, gtfs_time_to_sec

NEEDED = ["routes", "trips", "stop_times", "stops", "calendar", "calendar_dates", "frequencies"]
INDIA_LAT, INDIA_LON = (6, 37), (68, 98)


def load_raw(city_dir):
    """Load the GTFS files Module 2 needs (shapes.txt is read separately, only if present)."""
    ig.ensure_extracted(city_dir)
    return {n: df for n in NEEDED if (df := ig.read_file(city_dir, n)) is not None}


class CleanLog:
    def __init__(self, city):
        self.city, self.rows = city, []

    def add(self, table, step, before, after, reason, action="removed"):
        self.rows.append(dict(city=self.city, table=table, step=step, rows_before=int(before), rows_after=int(after),
                              rows_changed=int(abs(before - after)), action=action, reason=reason))

    def frame(self):
        return pd.DataFrame(self.rows)


def _nonblank(s):
    return s.notna() & (s.astype("string").str.strip() != "")


def clean_city(raw, city, bus_only=True):
    """Return (clean_tables, cleaning_log). `raw` comes from load_raw()."""
    L = CleanLog(city)
    # ------------------------------------------------------------ routes
    r = raw["routes"].copy()
    n = len(r); r = r.drop_duplicates("route_id")
    L.add("routes", "drop duplicate route_id", n, len(r), "route_id must be unique; first occurrence kept")
    if bus_only and "route_type" in r.columns:
        rt = pd.to_numeric(r.route_type, errors="coerce")
        bus = (rt == 3) | rt.between(700, 799) | rt.between(200, 299) | (rt == 11)
        if bus.any() and (~bus).any():
            n = len(r); r = r[bus]
            L.add("routes", "exclude non-bus route_type", n, len(r),
                  "Project scope is public bus routes; metro/rail/ferry rows excluded here (they remain in the raw files)")
    short = r["route_short_name"] if "route_short_name" in r else pd.Series(np.nan, index=r.index)
    long_ = r["route_long_name"] if "route_long_name" in r else pd.Series(np.nan, index=r.index)
    r["route_name"] = np.where(_nonblank(short), short.astype("string").str.strip(),
                               np.where(_nonblank(long_), long_.astype("string").str.strip(), r.route_id))
    L.add("routes", "derive route_name (short name, else long name, else route_id)",
          int((~_nonblank(short) & ~_nonblank(long_)).sum()), 0,
          "Display label only; no source value is overwritten. Count = routes that have neither name", action="derived")
    # ------------------------------------------------------------ trips
    t = raw["trips"].copy()
    n = len(t); t = t.drop_duplicates("trip_id")
    L.add("trips", "drop duplicate trip_id", n, len(t), "trip_id must be unique; first occurrence kept")
    n = len(t); t = t[t.route_id.isin(r.route_id)]
    L.add("trips", "drop trips whose route is not in the cleaned routes", n, len(t),
          "Orphan trips, or trips of excluded non-bus routes, cannot be analysed")
    # ------------------------------------------------------------ stops
    s = raw["stops"].copy()
    n = len(s); s = s.drop_duplicates("stop_id")
    L.add("stops", "drop duplicate stop_id", n, len(s), "stop_id must be unique; first occurrence kept")
    s["stop_lat"] = pd.to_numeric(s.stop_lat, errors="coerce"); s["stop_lon"] = pd.to_numeric(s.stop_lon, errors="coerce")
    ok = s.stop_lat.between(*INDIA_LAT) & s.stop_lon.between(*INDIA_LON) & ~((s.stop_lat == 0) & (s.stop_lon == 0))
    n = len(s); s = s[ok]
    L.add("stops", "drop stops with missing / non-numeric / out-of-India / (0,0) coordinates", n, len(s),
          "A stop that cannot be located cannot be used for distances or maps")
    if "stop_name" not in s.columns:
        s["stop_name"] = s.stop_id
    # ------------------------------------------------------------ stop_times
    cols = [c for c in ["trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"] if c in raw["stop_times"].columns]
    st = raw["stop_times"][cols].copy()
    st["stop_sequence"] = pd.to_numeric(st.stop_sequence, errors="coerce")
    n = len(st); st = st.dropna(subset=["stop_sequence"])
    L.add("stop_times", "drop rows with non-numeric stop_sequence", n, len(st), "Order of stops within the trip is unknown")
    arr = gtfs_time_to_sec(st.arrival_time) if "arrival_time" in st else pd.Series(np.nan, index=st.index)
    dep = gtfs_time_to_sec(st.departure_time) if "departure_time" in st else pd.Series(np.nan, index=st.index)
    L.add("stop_times", "fill a missing arrival (or departure) with the other time of the same stop visit",
          int((arr.isna() ^ dep.isna()).sum()), 0, "Dwell time 0 assumed only for that stop visit; no interpolation between stops", action="filled")
    st["arr_s"], st["dep_s"] = arr.fillna(dep), dep.fillna(arr)
    st = st.drop(columns=[c for c in ("arrival_time", "departure_time") if c in st])
    n = len(st); st = st.dropna(subset=["arr_s", "dep_s"])
    L.add("stop_times", "drop rows where both times are missing or unparseable", n, len(st), "No timing information to use")
    n = len(st); st = st[st.trip_id.isin(t.trip_id)]
    L.add("stop_times", "drop rows whose trip is not in the cleaned trips", n, len(st), "Orphan rows or rows of excluded routes")
    n = len(st); st = st[st.stop_id.isin(s.stop_id)]
    L.add("stop_times", "drop rows whose stop is not in the cleaned stops", n, len(st), "Stop unknown or without valid coordinates")
    n = len(st); st = st.drop_duplicates(["trip_id", "stop_sequence"])
    L.add("stop_times", "drop duplicate (trip_id, stop_sequence)", n, len(st), "Same stop position listed twice; first kept")
    fr = raw.get("frequencies")
    if fr is not None and len(fr):
        nt, ns = len(t), len(st)
        f = expand_frequencies(dict(frequencies=fr, trips=t, stop_times=st))
        t, st = f["trips"], f["stop_times"]
        L.add("trips", "expand frequencies.txt templates into explicit trips", nt, len(t),
              "Feed gives 'a bus every N seconds'; without expansion trip counts would be far too low", action="expanded")
        L.add("stop_times", "rows after frequency expansion", ns, len(st), "Consequence of the expansion above", action="expanded")
    st = st.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
    n = len(t); t = t[t.trip_id.isin(st.trip_id)]
    L.add("trips", "drop trips with no stop_times", n, len(t), "Hour, duration and length cannot be derived without stop times")
    prev = st.trip_id.shift()
    back = (st.arr_s.diff() < 0) & (st.trip_id == prev)
    bad = set(st.trip_id[back])
    L.add("trips", "FLAG trips whose arrival times go backwards", len(bad), 0,
          "Kept; marked in trip_features.time_backwards for review instead of being silently altered", action="flagged")
    L.add("routes", "FLAG routes with no scheduled trip after cleaning", int((~r.route_id.isin(t.route_id)).sum()), 0,
          "Kept in routes table; they simply have no scheduled service in this feed", action="flagged")
    # ------------------------------------------------------------ calendar
    cal = raw.get("calendar")
    if cal is not None:
        cal = cal.copy()
        for c in ("start_date", "end_date"):
            cal[c] = pd.to_datetime(cal[c].astype(str), format="%Y%m%d", errors="coerce")
        L.add("calendar", "parse start_date / end_date (invalid -> NaT)", int(cal.start_date.isna().sum() + cal.end_date.isna().sum()), 0,
              "YYYYMMDD converted to dates; nothing removed", action="parsed")
    clean = dict(routes=r, trips=t, stops=s, stop_times=st, calendar=cal, time_backwards_trips=bad)
    return clean, L.frame()
