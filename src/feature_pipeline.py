"""
RouteRanker Reusable GTFS Feature Engineering Pipeline
------------------------------------------------------
Extracted verbatim from Module 2 (RAW DATASET/module2_feature_engineering.ipynb)
without altering any feature definitions, time rules, headway calculations,
route length methods, or column ordering.
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd

# Core and optional GTFS filenames
CORE_FILES = ["routes", "trips", "stop_times", "stops", "calendar"]
OPTIONAL_FILES = ["shapes", "frequencies"]

# Identifier columns read as strings and prefixed with city_
ID_COLS = {
    "routes": ["route_id", "agency_id"],
    "trips": ["route_id", "trip_id", "service_id", "shape_id"],
    "stop_times": ["trip_id", "stop_id"],
    "stops": ["stop_id", "zone_id", "parent_station"],
    "calendar": ["service_id"],
}

PRIMARY_ID = {"routes": "route_id", "trips": "trip_id", "stops": "stop_id"}

WEEKDAY_COLS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
WEEKEND_COLS = ["saturday", "sunday"]
WEEKDAYS_SET = set(WEEKDAY_COLS)
WEEKENDS_SET = set(WEEKEND_COLS)

TIME_PATTERN = re.compile(r"^\d+:\d{2}:\d{2}$")
LAT_MIN, LAT_MAX = 6.0, 38.0
LON_MIN, LON_MAX = 68.0, 98.0

FINAL_COLS = [
    "city",
    "route_id",
    "original_route_id",
    "route_short_name",
    "route_long_name",
    "trip_count",
    "stop_count",
    "route_length_km",
    "length_method",
    "median_headway_min",
    "trips_morning",
    "trips_afternoon",
    "trips_evening",
    "trips_night",
    "trips_weekday",
    "trips_weekend",
    "first_departure_hour",
    "last_departure_hour",
    "service_span_hours",
    "operating_days",
]


def check_optional_files(city_path: Path, ext: str = ".txt") -> dict:
    """Check which optional GTFS files (shapes, frequencies) exist in city_path."""
    return {opt: (Path(city_path) / f"{opt}{ext}").exists() for opt in OPTIONAL_FILES}


def load_city_gtfs(city: str, city_path: Path, ext: str = ".txt", prefix_ids: bool = True):
    """
    Load the five core GTFS tables for a city, add 'city' column, and prefix IDs.

    Returns
    -------
    city_data : dict[str, pd.DataFrame | None]
    optional_status : dict[str, bool]
    file_metadata : list[dict]
    """
    city_path = Path(city_path)
    city_data = {}
    file_metadata = []

    for file_name in CORE_FILES:
        file_path = city_path / f"{file_name}{ext}"
        try:
            header_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            dtype_map = {c: str for c in ID_COLS.get(file_name, []) if c in header_cols}
            df = pd.read_csv(
                file_path, dtype=dtype_map, low_memory=False, keep_default_na=True
            )
            if prefix_ids:
                df.insert(0, "city", city)
                for col in ID_COLS.get(file_name, []):
                    if col in df.columns:
                        df[col] = city + "_" + df[col].astype(str)
            city_data[file_name] = df
            file_metadata.append(
                {
                    "file": f"{file_name}{ext}",
                    "rows": len(df),
                    "cols": df.shape[1],
                    "columns": list(df.columns),
                    "dtypes": {c: str(dt) for c, dt in df.dtypes.items()},
                }
            )
        except FileNotFoundError:
            city_data[file_name] = None
            file_metadata.append(
                {
                    "file": f"{file_name}{ext}",
                    "rows": None,
                    "cols": None,
                    "columns": [],
                    "dtypes": {},
                }
            )

    optional_status = check_optional_files(city_path, ext=ext)
    return city_data, optional_status, file_metadata


def run_data_quality_checks(city: str, city_data: dict) -> dict:
    """
    Run Module 2 Phase 2 data quality checks on one city (report only, no mutations):
    missing values, duplicate rows/primary IDs, orphan cross-file IDs,
    time format & >=24h counts, India bounding-box coordinates, calendar date range.
    """
    # 1. Missing values
    missing_records = []
    for file_name in CORE_FILES:
        df = city_data.get(file_name)
        if df is None:
            continue
        mc = df.isnull().sum()
        mc = mc[mc > 0]
        for col, cnt in mc.items():
            pct = round(100.0 * cnt / len(df), 2)
            missing_records.append(
                {
                    "city": city,
                    "file": file_name,
                    "column": col,
                    "missing_count": int(cnt),
                    "missing_pct": pct,
                }
            )
    missing_df = pd.DataFrame(missing_records)

    # 2. Duplicates
    dup_records = []
    for file_name in CORE_FILES:
        df = city_data.get(file_name)
        if df is None:
            continue
        n_dup = int(df.duplicated().sum())
        dup_records.append(
            {"city": city, "file": file_name, "check": "duplicate_rows", "count": n_dup}
        )
        if file_name in PRIMARY_ID:
            id_col = PRIMARY_ID[file_name]
            if id_col in df.columns:
                n_id = int(df[id_col].duplicated().sum())
                dup_records.append(
                    {
                        "city": city,
                        "file": file_name,
                        "check": f"duplicate_{id_col}",
                        "count": n_id,
                    }
                )
    dup_df = pd.DataFrame(dup_records)

    # 3. Orphan cross-file IDs
    xref_checks = [
        ("trips", "route_id", "routes", "route_id"),
        ("stop_times", "trip_id", "trips", "trip_id"),
        ("stop_times", "stop_id", "stops", "stop_id"),
        ("trips", "service_id", "calendar", "service_id"),
    ]
    xref_records = []
    for child_file, child_col, parent_file, parent_col in xref_checks:
        cdf = city_data.get(child_file)
        pdf = city_data.get(parent_file)
        if cdf is None or pdf is None:
            continue
        if child_col not in cdf.columns or parent_col not in pdf.columns:
            xref_records.append(
                {
                    "city": city,
                    "child_file": child_file,
                    "child_col": child_col,
                    "parent_file": parent_file,
                    "orphan_count": None,
                    "orphan_pct": None,
                    "note": "col missing",
                }
            )
            continue
        valid = set(pdf[parent_col].dropna().unique())
        vals = cdf[child_col]
        mask = ~vals.isin(valid) & vals.notna()
        n_orph = int(mask.sum())
        total = int(vals.notna().sum())
        pct = round(100.0 * n_orph / total, 2) if total > 0 else 0.0
        xref_records.append(
            {
                "city": city,
                "child_file": child_file,
                "child_col": child_col,
                "parent_file": parent_file,
                "orphan_count": n_orph,
                "orphan_pct": pct,
                "note": "",
            }
        )
    xref_df = pd.DataFrame(xref_records)

    # 4. Time format validation
    time_records = []
    st = city_data.get("stop_times")
    if st is not None:
        for col in ["arrival_time", "departure_time"]:
            if col not in st.columns:
                time_records.append(
                    {
                        "city": city,
                        "column": col,
                        "total": None,
                        "missing": None,
                        "bad_format": None,
                        "gte_24h": None,
                        "note": "absent",
                    }
                )
                continue
            n_total = len(st)
            n_missing = int(st[col].isnull().sum())
            non_null = st[col].dropna().astype(str)
            bad_mask = ~non_null.str.match(TIME_PATTERN)
            n_bad = int(bad_mask.sum())
            valid_fmt = non_null[~bad_mask]
            gte24 = int(valid_fmt.str.split(":", n=1).str[0].astype(int).ge(24).sum())
            time_records.append(
                {
                    "city": city,
                    "column": col,
                    "total": n_total,
                    "missing": n_missing,
                    "bad_format": n_bad,
                    "gte_24h": gte24,
                    "note": "",
                }
            )
    time_df = pd.DataFrame(time_records)

    # 5. Stop coordinates (India bounding box)
    sdf = city_data.get("stops")
    coord_summary = None
    if sdf is not None:
        n = len(sdf)
        if "stop_lat" in sdf.columns:
            lat = pd.to_numeric(sdf["stop_lat"], errors="coerce")
            ml = int(lat.isnull().sum())
            bl = int(((lat < LAT_MIN) | (lat > LAT_MAX)).sum())
            lat_min_val, lat_max_val = float(lat.min()), float(lat.max())
        else:
            ml = bl = None
            lat_min_val = lat_max_val = None
        if "stop_lon" in sdf.columns:
            lon = pd.to_numeric(sdf["stop_lon"], errors="coerce")
            mn = int(lon.isnull().sum())
            bn = int(((lon < LON_MIN) | (lon > LON_MAX)).sum())
            lon_min_val, lon_max_val = float(lon.min()), float(lon.max())
        else:
            mn = bn = None
            lon_min_val = lon_max_val = None
        coord_summary = {
            "city": city,
            "total_stops": n,
            "missing_lat": ml,
            "missing_lon": mn,
            "bad_lat": bl,
            "bad_lon": bn,
            "lat_min": lat_min_val,
            "lat_max": lat_max_val,
            "lon_min": lon_min_val,
            "lon_max": lon_max_val,
        }

    # 6. Calendar date range
    cdf = city_data.get("calendar")
    cal_summary = None
    if cdf is not None:
        row = {"city": city, "rows": len(cdf)}
        parsed = {}
        for col in ["start_date", "end_date"]:
            if col not in cdf.columns:
                row.update(
                    {f"{col}_min": "N/A", f"{col}_max": "N/A", f"{col}_parse_errors": None}
                )
                parsed[col] = None
                continue
            p = pd.to_datetime(cdf[col].astype(str), format="%Y%m%d", errors="coerce")
            parsed[col] = p
            row[f"{col}_min"] = str(p.min().date()) if p.notna().any() else "N/A"
            row[f"{col}_max"] = str(p.max().date()) if p.notna().any() else "N/A"
            row[f"{col}_parse_errors"] = int(p.isnull().sum())
        if parsed.get("start_date") is not None and parsed.get("end_date") is not None:
            both = parsed["start_date"].notna() & parsed["end_date"].notna()
            row["end_before_start"] = int(
                (parsed["end_date"][both] < parsed["start_date"][both]).sum()
            )
        else:
            row["end_before_start"] = None
        cal_summary = row

    return {
        "missing": missing_df,
        "duplicates": dup_df,
        "orphans": xref_df,
        "times": time_df,
        "coordinates": coord_summary,
        "calendar": cal_summary,
    }


def gtfs_to_seconds(time_str):
    """
    Convert a GTFS time string HH:MM:SS to total seconds since midnight.
    Hours can be 24 or more (e.g. 25:10:00 for overnight trips).
    Returns float('nan') for any invalid or missing value.
    """
    try:
        if pd.isna(time_str):
            return float("nan")
    except TypeError:
        pass

    try:
        parts = str(time_str).strip().split(":")
        if len(parts) != 3:
            return float("nan")
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        if not (0 <= m <= 59 and 0 <= s <= 59):
            return float("nan")
        return float(h * 3600 + m * 60 + s)
    except (ValueError, AttributeError):
        return float("nan")


def assign_time_period(dep_hour):
    """
    Assign a time-period label based on the normalised departure hour (0-23).
      morning   05:00 - 11:59   dep_hour  5 to 11
      afternoon 12:00 - 16:59   dep_hour 12 to 16
      evening   17:00 - 20:59   dep_hour 17 to 20
      night     21:00 - 04:59   dep_hour 21-23 or 0-4
    """
    if pd.isna(dep_hour):
        return float("nan")
    h = int(dep_hour)
    if 5 <= h <= 11:
        return "morning"
    if 12 <= h <= 16:
        return "afternoon"
    if 17 <= h <= 20:
        return "evening"
    return "night"


def add_stop_time_features(st_df: pd.DataFrame) -> pd.DataFrame:
    """Add arr_seconds, dep_seconds, dep_hour_raw, dep_hour, dep_minute, next_day_flag, time_period."""
    st = st_df.copy()
    if "arrival_time" in st.columns:
        arr_map = {v: gtfs_to_seconds(v) for v in st["arrival_time"].unique()}
        st["arr_seconds"] = st["arrival_time"].map(arr_map).astype(float)
    else:
        st["arr_seconds"] = float("nan")

    if "departure_time" in st.columns:
        dep_map = {v: gtfs_to_seconds(v) for v in st["departure_time"].unique()}
        st["dep_seconds"] = st["departure_time"].map(dep_map).astype(float)
    else:
        st["dep_seconds"] = float("nan")

    st["dep_hour_raw"] = st["dep_seconds"] // 3600
    st["dep_hour"] = st["dep_hour_raw"] % 24
    st["dep_minute"] = (st["dep_seconds"] % 3600) // 60
    st["next_day_flag"] = st["dep_hour_raw"] >= 24
    period_map = {v: assign_time_period(v) for v in st["dep_hour"].unique()}
    st["time_period"] = st["dep_hour"].map(period_map)
    return st


def classify_day_type(row) -> str:
    """Classify a calendar row into weekday_only, weekend_only, all_days, or mixed."""
    wd_vals = [row.get(c, 0) for c in WEEKDAY_COLS]
    we_vals = [row.get(c, 0) for c in WEEKEND_COLS]
    has_wd = any(v == 1 for v in wd_vals)
    has_we = any(v == 1 for v in we_vals)
    no_wd = all(v == 0 for v in wd_vals)
    no_we = all(v == 0 for v in we_vals)

    if has_wd and no_we:
        return "weekday_only"
    if has_we and no_wd:
        return "weekend_only"
    if has_wd and has_we:
        all_cols = WEEKDAY_COLS + WEEKEND_COLS
        if all(row.get(c, 0) == 1 for c in all_cols):
            return "all_days"
        return "mixed"
    return "mixed"


def get_operating_days(row) -> str:
    """Return a comma-separated list of day names where value = 1."""
    active = [d for d in WEEKDAY_COLS + WEEKEND_COLS if row.get(d, 0) == 1]
    return ",".join(active) if active else "none"


def add_calendar_day_features(cal_df: pd.DataFrame, trips_df: pd.DataFrame):
    """Compute day_type and operating_days on calendar and left-join onto trips."""
    cal = cal_df.copy()
    trips = trips_df.copy()

    avail_wd = [c for c in WEEKDAY_COLS if c in cal.columns]
    avail_we = [c for c in WEEKEND_COLS if c in cal.columns]

    if not avail_wd and not avail_we:
        cal["day_type"] = "unknown"
        cal["operating_days"] = "unknown"
    else:
        cal["day_type"] = cal.apply(classify_day_type, axis=1)
        cal["operating_days"] = cal.apply(get_operating_days, axis=1)

    lookup = cal.set_index("service_id")[["day_type", "operating_days"]]
    drop_existing = [c for c in ["day_type", "operating_days"] if c in trips.columns]
    if drop_existing:
        trips.drop(columns=drop_existing, inplace=True)
    trips = trips.merge(lookup, on="service_id", how="left")
    return cal, trips


def extract_trip_starts(st_df: pd.DataFrame, trips_df: pd.DataFrame) -> pd.DataFrame:
    """Extract each trip's start departure time at the lowest stop_sequence and merge onto trips."""
    trips = trips_df.copy()
    valid_st = st_df[st_df["dep_seconds"].notna()].copy()
    valid_st["stop_sequence_num"] = pd.to_numeric(valid_st["stop_sequence"], errors="coerce")

    first_stops = valid_st.sort_values(["trip_id", "stop_sequence_num"]).drop_duplicates(
        subset=["trip_id"], keep="first"
    )

    trip_starts = first_stops[["trip_id", "dep_seconds", "dep_hour", "dep_minute", "time_period"]].copy()
    trip_starts.rename(
        columns={
            "dep_seconds": "start_seconds",
            "dep_hour": "start_hour",
            "dep_minute": "start_minute",
            "time_period": "start_time_period",
        },
        inplace=True,
    )

    drop_existing = [c for c in trip_starts.columns if c != "trip_id" and c in trips.columns]
    if drop_existing:
        trips.drop(columns=drop_existing, inplace=True)

    return trips.merge(trip_starts, on="trip_id", how="left")


def compute_route_base_features(routes_df: pd.DataFrame, trips_df: pd.DataFrame, st_df: pd.DataFrame) -> pd.DataFrame:
    """Compute distinct trip_count and distinct stop_count per route (Module 2 Phase 4)."""
    trip_counts = (
        trips_df.groupby("route_id")["trip_id"].nunique().reset_index(name="trip_count")
    )

    if st_df is not None and "stop_id" in st_df.columns:
        trips_sub = trips_df[["route_id", "trip_id"]].dropna()
        st_sub = st_df[["trip_id", "stop_id"]].dropna()
        merged_route_stops = trips_sub.merge(st_sub, on="trip_id", how="inner")
        stop_counts = (
            merged_route_stops.groupby("route_id")["stop_id"]
            .nunique()
            .reset_index(name="stop_count")
        )
    else:
        stop_counts = pd.DataFrame(columns=["route_id", "stop_count"])

    base_cols = ["city", "route_id"]
    for col in ["route_short_name", "route_long_name", "route_type"]:
        if col in routes_df.columns:
            base_cols.append(col)

    city_route_feats = routes_df[base_cols].copy()
    city_route_feats = city_route_feats.merge(trip_counts, on="route_id", how="left")
    city_route_feats = city_route_feats.merge(stop_counts, on="route_id", how="left")
    return city_route_feats


def compute_route_headways(trips_df: pd.DataFrame) -> pd.DataFrame:
    """Compute route-level median/min/max headway_min and period headways (Module 2 Phase 5)."""
    valid = trips_df[trips_df["start_seconds"].notna()].copy()
    if len(valid) == 0:
        return pd.DataFrame(
            columns=[
                "route_id",
                "median_headway_min",
                "min_headway_min",
                "max_headway_min",
                "hw_morning_median_min",
                "hw_afternoon_median_min",
                "hw_evening_median_min",
                "hw_night_median_min",
            ]
        )

    group_cols = ["route_id", "day_type"] if "day_type" in valid.columns else ["route_id"]
    if "direction_id" in valid.columns:
        group_cols.append("direction_id")

    valid = valid.sort_values(group_cols + ["start_seconds"]).copy()
    valid["headway_min"] = valid.groupby(group_cols)["start_seconds"].diff() / 60.0

    route_hw = (
        valid.groupby("route_id")["headway_min"]
        .agg(
            median_headway_min="median",
            min_headway_min="min",
            max_headway_min="max",
        )
        .reset_index()
    )

    if "start_time_period" in valid.columns:
        period_hw = (
            valid.groupby(["route_id", "start_time_period"])["headway_min"]
            .median()
            .unstack()
            .reset_index()
        )
        for p in ["morning", "afternoon", "evening", "night"]:
            if p in period_hw.columns:
                period_hw.rename(columns={p: f"hw_{p}_median_min"}, inplace=True)
            else:
                period_hw[f"hw_{p}_median_min"] = float("nan")
        return route_hw.merge(period_hw, on="route_id", how="left")

    return route_hw


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometers between points (Earth mean radius 6371.0088 km)."""
    R = 6371.0088
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * np.arcsin(np.clip(np.sqrt(a), 0.0, 1.0))
    return R * c


def calculate_path_length_km(df: pd.DataFrame, lat_col: str, lon_col: str) -> float:
    """Sum Haversine distances between consecutive coordinate pairs in an ordered DataFrame."""
    if df is None or len(df) < 2:
        return float("nan")

    lats = pd.to_numeric(df[lat_col], errors="coerce").values
    lons = pd.to_numeric(df[lon_col], errors="coerce").values

    if np.isnan(lats).any() or np.isnan(lons).any():
        return float("nan")

    step_dists = haversine_distance_km(lats[:-1], lons[:-1], lats[1:], lons[1:])
    return float(np.sum(step_dists))


def compute_route_lengths(
    city: str,
    city_path: Path,
    routes_df: pd.DataFrame,
    trips_df: pd.DataFrame,
    st_df: pd.DataFrame,
    stops_df: pd.DataFrame,
    ext: str = ".txt",
):
    """
    Compute route_length_km and length_method ('shape' or 'stop_straight_line_estimate').
    Exact Module 2 Phase 6 implementation.
    """
    shape_file = Path(city_path) / f"shapes{ext}"
    has_shapes = (
        shape_file.exists()
        and ("shape_id" in trips_df.columns)
        and (trips_df["shape_id"].notna().sum() > 0)
    )

    route_length_map = {}
    length_method_map = {}

    if has_shapes:
        try:
            raw_shapes = pd.read_csv(shape_file, low_memory=False)
            raw_shapes["shape_id"] = city + "_" + raw_shapes["shape_id"].astype(str)
            raw_shapes["shape_pt_sequence"] = pd.to_numeric(
                raw_shapes["shape_pt_sequence"], errors="coerce"
            )
            raw_shapes["shape_pt_lat"] = pd.to_numeric(
                raw_shapes["shape_pt_lat"], errors="coerce"
            )
            raw_shapes["shape_pt_lon"] = pd.to_numeric(
                raw_shapes["shape_pt_lon"], errors="coerce"
            )

            shape_lengths = {}
            for sid, grp in raw_shapes.groupby("shape_id"):
                sorted_grp = grp.sort_values("shape_pt_sequence")
                shape_lengths[sid] = calculate_path_length_km(
                    sorted_grp, "shape_pt_lat", "shape_pt_lon"
                )

            valid_trip_shapes = trips_df[
                trips_df["shape_id"].notna()
                & (trips_df["shape_id"] != "")
                & (trips_df["shape_id"] != f"{city}_nan")
            ]
            for r_id, grp in valid_trip_shapes.groupby("route_id"):
                modes = grp["shape_id"].mode()
                if not modes.empty:
                    rep_shape = modes.iloc[0]
                    if rep_shape in shape_lengths and pd.notna(shape_lengths[rep_shape]):
                        route_length_map[r_id] = shape_lengths[rep_shape]
                        length_method_map[r_id] = "shape"
        except Exception as exc:
            print(f"  {city}: Error reading shapes ({exc}), falling back to stops.")

    if (
        st_df is not None
        and stops_df is not None
        and "stop_lat" in stops_df.columns
        and "stop_lon" in stops_df.columns
    ):
        stops_coords = stops_df[["stop_id", "stop_lat", "stop_lon"]].copy()
        stops_coords["stop_lat"] = pd.to_numeric(stops_coords["stop_lat"], errors="coerce")
        stops_coords["stop_lon"] = pd.to_numeric(stops_coords["stop_lon"], errors="coerce")

        st_clean = st_df[["trip_id", "stop_id", "stop_sequence"]].copy()
        st_clean["stop_sequence"] = pd.to_numeric(st_clean["stop_sequence"], errors="coerce")
        st_with_coords = st_clean.merge(stops_coords, on="stop_id", how="left")

        trip_stop_counts = (
            st_with_coords.dropna(subset=["stop_lat", "stop_lon"])
            .groupby("trip_id")["stop_sequence"]
            .count()
        )

        routes_to_fill = [r for r in routes_df["route_id"].unique() if r not in route_length_map]
        trips_to_fill = trips_df[trips_df["route_id"].isin(routes_to_fill)]

        rep_trips_map = {}
        for r_id, grp in trips_to_fill.groupby("route_id"):
            route_trip_ids = grp["trip_id"].values
            avail_counts = trip_stop_counts.reindex(route_trip_ids).dropna()
            if not avail_counts.empty:
                rep_trips_map[r_id] = avail_counts.idxmax()
            else:
                rep_trips_map[r_id] = None

        selected_tids = {tid for tid in rep_trips_map.values() if tid is not None}
        st_rep_subset = st_with_coords[st_with_coords["trip_id"].isin(selected_tids)]
        rep_groups = {
            tid: g.sort_values("stop_sequence")
            for tid, g in st_rep_subset.groupby("trip_id")
        }

        for r_id, rep_trip_id in rep_trips_map.items():
            if rep_trip_id is not None and rep_trip_id in rep_groups:
                calc_len = calculate_path_length_km(
                    rep_groups[rep_trip_id], "stop_lat", "stop_lon"
                )
                route_length_map[r_id] = calc_len if pd.notna(calc_len) else float("nan")
                length_method_map[r_id] = "stop_straight_line_estimate"
            else:
                route_length_map[r_id] = float("nan")
                length_method_map[r_id] = "stop_straight_line_estimate"

    return route_length_map, length_method_map


def has_weekday(days_str) -> bool:
    if not isinstance(days_str, str):
        return False
    return len(set(days_str.lower().split(",")) & WEEKDAYS_SET) > 0


def has_weekend(days_str) -> bool:
    if not isinstance(days_str, str):
        return False
    return len(set(days_str.lower().split(",")) & WEEKENDS_SET) > 0


def union_days(series) -> str:
    active_days = set()
    for s in series.dropna():
        if isinstance(s, str) and s not in ["unknown", "none"]:
            active_days.update(s.lower().split(","))
    day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    ordered = [d for d in day_order if d in active_days]
    return ",".join(ordered) if ordered else "unknown"


def assemble_route_features(city: str, rf_base: pd.DataFrame, trips_df: pd.DataFrame) -> pd.DataFrame:
    """Assemble the strict 20-column route feature table for one city (Module 2 Phase 7)."""
    rf = rf_base.copy()
    prefix = city + "_"
    rf["original_route_id"] = rf["route_id"].apply(
        lambda x: str(x)[len(prefix) :] if str(x).startswith(prefix) else str(x)
    )
    rf["route_id"] = rf["route_id"].astype(str)
    rf["original_route_id"] = rf["original_route_id"].astype(str)
    rf["city"] = city

    if "route_short_name" not in rf.columns:
        rf["route_short_name"] = float("nan")
    if "route_long_name" not in rf.columns:
        rf["route_long_name"] = float("nan")

    if trips_df is not None and not trips_df.empty:
        trips_valid = trips_df.copy()

        if "start_time_period" in trips_valid.columns:
            tp_pivot = (
                trips_valid.dropna(subset=["start_time_period"])
                .groupby(["route_id", "start_time_period"])["trip_id"]
                .nunique()
                .unstack(fill_value=0)
                .reset_index()
            )
            for p in ["morning", "afternoon", "evening", "night"]:
                if p not in tp_pivot.columns:
                    tp_pivot[p] = 0
            tp_pivot.rename(
                columns={
                    "morning": "trips_morning",
                    "afternoon": "trips_afternoon",
                    "evening": "trips_evening",
                    "night": "trips_night",
                },
                inplace=True,
            )
        else:
            tp_pivot = pd.DataFrame(
                columns=[
                    "route_id",
                    "trips_morning",
                    "trips_afternoon",
                    "trips_evening",
                    "trips_night",
                ]
            )

        if "operating_days" in trips_valid.columns:
            trips_valid["is_wd"] = trips_valid["operating_days"].apply(has_weekday)
            trips_valid["is_we"] = trips_valid["operating_days"].apply(has_weekend)
            wd_counts = (
                trips_valid[trips_valid["is_wd"]]
                .groupby("route_id")["trip_id"]
                .nunique()
                .reset_index(name="trips_weekday")
            )
            we_counts = (
                trips_valid[trips_valid["is_we"]]
                .groupby("route_id")["trip_id"]
                .nunique()
                .reset_index(name="trips_weekend")
            )
        else:
            wd_counts = pd.DataFrame(columns=["route_id", "trips_weekday"])
            we_counts = pd.DataFrame(columns=["route_id", "trips_weekend"])

        if "start_seconds" in trips_valid.columns:
            span_stats = (
                trips_valid.dropna(subset=["start_seconds"])
                .groupby("route_id")["start_seconds"]
                .agg(min_s="min", max_s="max")
                .reset_index()
            )
            span_stats["first_departure_hour"] = span_stats["min_s"] // 3600
            span_stats["last_departure_hour"] = span_stats["max_s"] // 3600
            span_stats["service_span_hours"] = (
                (span_stats["max_s"] - span_stats["min_s"]) / 3600.0
            ).round(2)
        else:
            span_stats = pd.DataFrame(
                columns=[
                    "route_id",
                    "first_departure_hour",
                    "last_departure_hour",
                    "service_span_hours",
                ]
            )

        if "operating_days" in trips_valid.columns:
            route_days = (
                trips_valid.groupby("route_id")["operating_days"]
                .apply(union_days)
                .reset_index(name="operating_days")
            )
        else:
            route_days = pd.DataFrame(columns=["route_id", "operating_days"])
    else:
        tp_pivot = pd.DataFrame(
            columns=[
                "route_id",
                "trips_morning",
                "trips_afternoon",
                "trips_evening",
                "trips_night",
            ]
        )
        wd_counts = pd.DataFrame(columns=["route_id", "trips_weekday"])
        we_counts = pd.DataFrame(columns=["route_id", "trips_weekend"])
        span_stats = pd.DataFrame(
            columns=[
                "route_id",
                "first_departure_hour",
                "last_departure_hour",
                "service_span_hours",
            ]
        )
        route_days = pd.DataFrame(columns=["route_id", "operating_days"])

    for sub_df in [
        tp_pivot,
        wd_counts,
        we_counts,
        span_stats[
            ["route_id", "first_departure_hour", "last_departure_hour", "service_span_hours"]
        ],
        route_days,
    ]:
        overlap = [c for c in sub_df.columns if c != "route_id" and c in rf.columns]
        if overlap:
            rf.drop(columns=overlap, inplace=True)
        rf = rf.merge(sub_df, on="route_id", how="left")

    has_trips = rf["trip_count"].notna() & (rf["trip_count"] > 0)
    count_cols = [
        "trips_morning",
        "trips_afternoon",
        "trips_evening",
        "trips_night",
        "trips_weekday",
        "trips_weekend",
    ]
    for c in count_cols:
        if c in rf.columns:
            rf.loc[has_trips, c] = rf.loc[has_trips, c].fillna(0)

    rf["operating_days"] = rf["operating_days"].fillna("unknown")

    for col in FINAL_COLS:
        if col not in rf.columns:
            rf[col] = float("nan")

    out = rf[FINAL_COLS].copy()
    out["city"] = out["city"].astype(str)
    out["route_id"] = out["route_id"].astype(str)
    out["original_route_id"] = out["original_route_id"].astype(str)
    return out


def build_city_route_features(city: str, city_path: Path, ext: str = ".txt"):
    """
    End-to-end execution of Module 2 feature engineering for a single city.

    Returns
    -------
    final_features_df : pd.DataFrame (20 columns matching processed/route_features.csv)
    diagnostics : dict (optional_status, file_metadata, quality_checks, summary_flags)
    """
    city_data, optional_status, file_metadata = load_city_gtfs(
        city, city_path, ext=ext, prefix_ids=True
    )
    quality_checks = run_data_quality_checks(city, city_data)

    # Phase 3: Time features & calendar day_type
    city_data["stop_times"] = add_stop_time_features(city_data["stop_times"])
    city_data["calendar"], city_data["trips"] = add_calendar_day_features(
        city_data["calendar"], city_data["trips"]
    )

    # Phase 4: Route aggregation (trip_count, stop_count)
    rf = compute_route_base_features(
        city_data["routes"], city_data["trips"], city_data["stop_times"]
    )

    # Phase 5: Trip starts & headways
    city_data["trips"] = extract_trip_starts(city_data["stop_times"], city_data["trips"])
    combined_hw = compute_route_headways(city_data["trips"])
    rf = rf.merge(combined_hw, on="route_id", how="left")

    # Phase 6: Route lengths
    route_length_map, length_method_map = compute_route_lengths(
        city=city,
        city_path=city_path,
        routes_df=city_data["routes"],
        trips_df=city_data["trips"],
        st_df=city_data["stop_times"],
        stops_df=city_data["stops"],
        ext=ext,
    )
    rf["route_length_km"] = rf["route_id"].map(route_length_map)
    rf["length_method"] = rf["route_id"].map(length_method_map).fillna("unmeasured")
    rf["flag_too_short"] = rf["route_length_km"] < 0.5
    rf["flag_too_long"] = rf["route_length_km"] > 150.0
    rf["flag_length_review"] = rf["flag_too_short"] | rf["flag_too_long"]

    # Phase 7: Assemble strict 20-column schema
    final_df = assemble_route_features(city, rf, city_data["trips"])

    diagnostics = {
        "optional_status": optional_status,
        "file_metadata": file_metadata,
        "quality_checks": quality_checks,
        "length_review_flags": rf[
            ["route_id", "route_length_km", "length_method", "flag_too_short", "flag_too_long", "flag_length_review"]
        ],
    }
    return final_df, diagnostics
