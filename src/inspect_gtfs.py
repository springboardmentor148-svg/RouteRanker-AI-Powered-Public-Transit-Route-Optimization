"""Module 1: READ-ONLY inspection of raw GTFS feeds.

Nothing in here modifies, deletes or imputes data. It only loads files and *reports* what it finds
(missing values, duplicates, odd types, broken identifiers, unusual times/dates), as required by Module 1.
"""
import glob, os, zipfile
import numpy as np
import pandas as pd

REQUIRED = {  # file -> columns the GTFS spec requires (conditionally-required ones are checked separately)
    "routes": ["route_id", "route_type"],
    "trips": ["route_id", "service_id", "trip_id"],
    "stop_times": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
    "stops": ["stop_id", "stop_lat", "stop_lon"],
    "calendar": ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                 "sunday", "start_date", "end_date"],
}
OPTIONAL = ["calendar_dates", "frequencies", "shapes", "agency", "feed_info"]
ID_COLS = ["route_id", "trip_id", "stop_id", "service_id", "shape_id", "agency_id", "parent_station"]
IMPORTANT = {  # columns that matter most for this project
    "routes": "route_id, route_short_name, route_long_name, route_type",
    "trips": "route_id, service_id, trip_id, direction_id, shape_id",
    "stop_times": "trip_id, arrival_time, departure_time, stop_id, stop_sequence",
    "stops": "stop_id, stop_name, stop_lat, stop_lon",
    "calendar": "service_id, monday..sunday, start_date, end_date",
    "calendar_dates": "service_id, date, exception_type",
    "frequencies": "trip_id, start_time, end_time, headway_secs",
    "shapes": "shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence",
}
USEFULNESS = {
    "frequencies": "Lets feeds describe 'a bus every N seconds' instead of listing each trip; needed to count real trips/hour.",
    "shapes": "Exact road geometry of a route; gives true route length/maps (stop-to-stop distance is only an approximation).",
    "calendar_dates": "Date-specific exceptions (holidays / added or removed service); needed when calendar.txt is missing.",
    "agency": "Operator name/contact; useful for documentation and multi-operator cities.",
    "feed_info": "Feed publisher, version and validity dates; useful to judge how current the data is.",
}


# ---------------------------------------------------------------- locating / loading
def ensure_extracted(city_dir):
    """If a city folder only holds a .zip, extract its .txt files next to it (original zip is kept untouched)."""
    if os.path.exists(os.path.join(city_dir, "stop_times.txt")):
        return "already extracted"
    zips = glob.glob(os.path.join(city_dir, "*.zip"))
    if not zips:
        return "no data"
    with zipfile.ZipFile(zips[0]) as z:
        for n in z.namelist():
            if n.endswith(".txt"):
                with z.open(n) as src, open(os.path.join(city_dir, os.path.basename(n)), "wb") as dst:
                    dst.write(src.read())
    return f"extracted from {os.path.basename(zips[0])}"


def read_file(city_dir, name):
    p = os.path.join(city_dir, f"{name}.txt")
    if not os.path.exists(p):
        return None
    head = pd.read_csv(p, nrows=0, encoding="utf-8-sig")
    dtypes = {c: str for c in head.columns if c in ID_COLS}
    df = pd.read_csv(p, dtype=dtypes, low_memory=False, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df


def load_city(city_dir):
    ensure_extracted(city_dir)
    return {n: df for n in list(REQUIRED) + OPTIONAL
            if (df := read_file(city_dir, n)) is not None}


def to_seconds(s):
    p = s.astype("string").str.strip().str.split(":", expand=True)
    if p.shape[1] < 3:
        return pd.Series(np.nan, index=s.index)
    return (pd.to_numeric(p[0], errors="coerce") * 3600 + pd.to_numeric(p[1], errors="coerce") * 60
            + pd.to_numeric(p[2], errors="coerce"))


# ---------------------------------------------------------------- inventory
def file_inventory(city, tables):
    rows = []
    for n in list(REQUIRED) + OPTIONAL:
        df = tables.get(n)
        rows.append(dict(city=city, file=f"{n}.txt", kind="required" if n in REQUIRED else "optional",
                         available=df is not None, records=0 if df is None else len(df),
                         columns=0 if df is None else df.shape[1],
                         column_names="" if df is None else ", ".join(df.columns)))
    return rows


# ---------------------------------------------------------------- quality checks
def quality_checks(city, tables, today=None):
    """Return list of dict(city,file,check,count,total,note). Counts only; no data is changed."""
    today = today or pd.Timestamp.today().normalize()
    out = []

    def add(file, check, count, total=None, note=""):
        out.append(dict(city=city, file=file, check=check, count=int(count),
                        total=None if total is None else int(total),
                        pct=None if not total else round(100 * count / total, 2), note=note))

    # 1. missing files
    for n in REQUIRED:
        if n not in tables:
            add(f"{n}.txt", "required file missing", 1, note="Required by GTFS / by project plan")
    if "calendar" not in tables and "calendar_dates" in tables:
        add("calendar.txt", "calendar.txt absent but calendar_dates.txt present", 1,
            note="Weekday/weekend must be derived from calendar_dates")

    # 2. missing values in required columns + duplicate keys
    keys = {"routes": ["route_id"], "trips": ["trip_id"], "stops": ["stop_id"],
            "stop_times": ["trip_id", "stop_sequence"], "calendar": ["service_id"]}
    for n, cols in REQUIRED.items():
        df = tables.get(n)
        if df is None:
            continue
        for c in cols:
            if c not in df.columns:
                add(f"{n}.txt", f"required column '{c}' missing", 1)
            else:
                miss = df[c].isna().sum() + (df[c].astype("string").str.strip() == "").sum()
                if miss:
                    add(f"{n}.txt", f"empty/missing value in '{c}'", miss, len(df))
        k = [c for c in keys[n] if c in df.columns]
        if k:
            add(f"{n}.txt", f"duplicate key {k}", df.duplicated(k).sum(), len(df))
    r = tables.get("routes")
    if r is not None:
        names = [c for c in ("route_short_name", "route_long_name") if c in r.columns]
        if names:
            blank = r[names].isna().all(axis=1) | (r[names].astype("string").apply(lambda s: s.str.strip()).eq("").all(axis=1))
            add("routes.txt", "route has neither short nor long name", blank.sum(), len(r))
            if "route_short_name" in r.columns:
                add("routes.txt", "route_short_name shared by >1 route_id (directions/variants)",
                    r.route_short_name.duplicated(keep=False).sum() - r.route_short_name.isna().sum(), len(r),
                    "Not an error: one bus line is often split into several route_ids")
        if "route_type" in r.columns:
            rt = pd.to_numeric(r.route_type, errors="coerce")
            add("routes.txt", "route_type is not a bus code (3 / 700-799 / 200-299 / 11)",
                (~((rt == 3) | rt.between(700, 799) | rt.between(200, 299) | (rt == 11))).sum(), len(r),
                "Metro/rail/ferry rows mixed in with buses")

    # 3. referential integrity (identifier consistency)
    t, st, s, cal, cd = (tables.get(x) for x in ("trips", "stop_times", "stops", "calendar", "calendar_dates"))
    if t is not None and r is not None:
        add("trips.txt", "route_id not found in routes.txt", (~t.route_id.isin(r.route_id)).sum(), len(t))
        add("routes.txt", "route with no trips", (~r.route_id.isin(t.route_id)).sum(), len(r))
    if t is not None and (cal is not None or cd is not None):
        known = set(cal.service_id) if cal is not None else set()
        known |= set(cd.service_id) if cd is not None else set()
        add("trips.txt", "service_id not defined in calendar/calendar_dates", (~t.service_id.isin(known)).sum(), len(t))
    if st is not None and t is not None:
        add("stop_times.txt", "trip_id not found in trips.txt", (~st.trip_id.isin(t.trip_id)).sum(), len(st))
        add("trips.txt", "trip with no stop_times", (~t.trip_id.isin(st.trip_id)).sum(), len(t),
            "May be frequency-based templates" if "frequencies" in tables else "")
    if st is not None and s is not None:
        add("stop_times.txt", "stop_id not found in stops.txt", (~st.stop_id.isin(s.stop_id)).sum(), len(st))
        add("stops.txt", "stop never used in stop_times", (~s.stop_id.isin(st.stop_id)).sum(), len(s))

    # 4. unexpected data types / unusual coordinate values
    if s is not None and {"stop_lat", "stop_lon"} <= set(s.columns):
        lat, lon = pd.to_numeric(s.stop_lat, errors="coerce"), pd.to_numeric(s.stop_lon, errors="coerce")
        add("stops.txt", "stop_lat/stop_lon not numeric (non-empty)", ((lat.isna() | lon.isna()) & s.stop_lat.notna() & s.stop_lon.notna()).sum(), len(s))
        add("stops.txt", "coordinates are 0,0", ((lat == 0) & (lon == 0)).sum(), len(s))
        add("stops.txt", "coordinates outside India (lat 6-37, lon 68-98)",
            (lat.notna() & lon.notna() & ~(lat.between(6, 37) & lon.between(68, 98))).sum(), len(s))
    if st is not None and "stop_sequence" in st.columns:
        add("stop_times.txt", "stop_sequence not numeric", pd.to_numeric(st.stop_sequence, errors="coerce").isna().sum(), len(st))

    # 5. unusual time values
    if st is not None and {"arrival_time", "departure_time"} <= set(st.columns):
        arr, dep = to_seconds(st.arrival_time), to_seconds(st.departure_time)
        add("stop_times.txt", "arrival_time unparseable (non-empty)", (arr.isna() & st.arrival_time.notna()).sum(), len(st))
        add("stop_times.txt", "departure_time unparseable (non-empty)", (dep.isna() & st.departure_time.notna()).sum(), len(st))
        add("stop_times.txt", "time >= 24:00:00 (valid GTFS: trip runs past midnight)", (arr >= 86400).sum(), len(st),
            "Valid in GTFS; must be handled when extracting hour-of-day")
        add("stop_times.txt", "arrival later than departure at same stop", (arr > dep).sum(), len(st))
        seq = pd.to_numeric(st.stop_sequence, errors="coerce")
        o = pd.DataFrame({"trip": st.trip_id.values, "seq": seq.values, "arr": arr.values}).sort_values(["trip", "seq"])
        back = ((o.arr.diff() < 0) & (o.trip == o.trip.shift())).sum()
        add("stop_times.txt", "time goes backwards within a trip", back, len(st))
        same = ((o.arr.diff() == 0) & (o.trip == o.trip.shift())).sum()
        add("stop_times.txt", "identical arrival time at consecutive stops", same, len(st),
            "High values suggest times were interpolated/estimated by the publisher")

    # 6. unusual dates / calendar validity
    if cal is not None and {"start_date", "end_date"} <= set(cal.columns):
        sd = pd.to_datetime(cal.start_date.astype(str), format="%Y%m%d", errors="coerce")
        ed = pd.to_datetime(cal.end_date.astype(str), format="%Y%m%d", errors="coerce")
        add("calendar.txt", "invalid start/end date", (sd.isna() | ed.isna()).sum(), len(cal))
        add("calendar.txt", "start_date after end_date", (sd > ed).sum(), len(cal))
        add("calendar.txt", f"service already expired (end_date < {today.date()})", (ed < today).sum(), len(cal),
            f"calendar covers {sd.min().date() if sd.notna().any() else '?'} to {ed.max().date() if ed.notna().any() else '?'}")
        days = [d for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] if d in cal.columns]
        if days:
            n_days = cal[days].astype(str).apply(lambda c: c.eq("1")).sum(axis=1)
            add("calendar.txt", "service runs on no day of the week", (n_days == 0).sum(), len(cal))
            add("calendar.txt", "service runs all 7 days (no weekday/weekend distinction)", (n_days == 7).sum(), len(cal),
                f"{cal.service_id.nunique()} service_id(s) in calendar.txt")
    return out


def relationship_stats(city, tables):
    """Measured facts about how the files connect (used in the relationships report)."""
    r, t, st, s, cal = (tables.get(x) for x in ("routes", "trips", "stop_times", "stops", "calendar"))
    d = dict(city=city)
    if r is not None and t is not None:
        d["routes"] = len(r); d["trips"] = len(t)
        d["trips_per_route_median"] = float(t.groupby("route_id").size().median())
        d["trips_per_route_max"] = int(t.groupby("route_id").size().max())
    if st is not None and t is not None:
        d["stop_times"] = len(st)
        d["stops_per_trip_median"] = float(st.groupby("trip_id").size().median())
    if st is not None and s is not None:
        d["stops"] = len(s)
        d["stop_times_matching_stops_pct"] = round(100 * st.stop_id.isin(s.stop_id).mean(), 2)
    if t is not None and cal is not None:
        d["services_in_calendar"] = int(cal.service_id.nunique())
        d["trips_matching_calendar_pct"] = round(100 * t.service_id.isin(cal.service_id).mean(), 2)
    return d
