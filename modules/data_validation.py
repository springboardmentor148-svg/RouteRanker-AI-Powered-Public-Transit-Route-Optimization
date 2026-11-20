"""Validation of route tables (project data or user uploads). It REPORTS problems; it never silently changes or deletes data."""
import numpy as np
import pandas as pd

from src import inference as inf, preprocessing as pp


def read_upload(file):
    """Read an uploaded CSV / Excel file. Returns (DataFrame or None, error message or None)."""
    try:
        name = file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(file, dtype={"route_id": str, "route_name": str})
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file, dtype={"route_id": str, "route_name": str})
        else:
            return None, "Unsupported file type. Please upload a .csv or .xlsx file."
        if df.empty:
            return None, "The file is empty."
        return df, None
    except Exception as e:                                       # unreadable / corrupt file
        return None, f"The file could not be read: {e}"


def schema_table(df):
    return pd.DataFrame({"column": df.columns, "data type": df.dtypes.astype(str).values, "non-null": df.notna().sum().values,
                         "missing": df.isna().sum().values, "missing %": (100 * df.isna().mean()).round(1).values, "unique values": df.nunique().values})


def missing_columns(df):
    """Module-2 feature columns the models need but the table does not have."""
    derived = {c for c in pp.NUMERIC if c.startswith("share_")}
    needed = (set(pp.NUMERIC) - derived) | set(pp.ID_COLS) | {"peak_hour", "length_method", "trips_morning", "trips_afternoon", "trips_evening", "trips_night"}
    return sorted(needed - set(df.columns))


def quality_report(df):
    """Counts of problems found (nothing is changed). Missing values are undefined values - not zeros."""
    q = []
    if "route_id" in df and "city" in df:
        q.append(("duplicate (city, route_id)", int(df.duplicated(["city", "route_id"]).sum()), "should be 0"))
    if "n_trips" in df:
        q.append(("routes with missing or non-positive n_trips", int((df.n_trips.isna() | (df.n_trips <= 0)).sum()), "every route should have at least 1 trip"))
    if "length_km" in df:
        q.append(("routes with missing or negative length", int((df.length_km.isna() | (df.length_km < 0)).sum()), "length could not be estimated or is invalid"))
    if "avg_speed_kmh" in df:
        lo, hi = pp.SPEED_RANGE
        q.append((f"scheduled speed outside {lo}-{hi} km/h", int((df.avg_speed_kmh.notna() & ~df.avg_speed_kmh.between(lo, hi)).sum()), "impossible for a bus timetable: check length / times"))
    if "median_headway_min" in df:
        q.append(("routes without a headway (single departure time)", int(df.median_headway_min.isna().sum()), "undefined, not zero"))
    return pd.DataFrame(q, columns=["check", "routes", "meaning"])


def numeric_summary(df):
    num = df.select_dtypes("number")
    s = num.agg(["count", "min", "median", "mean", "std", "max"]).T
    return s.round(2)


def validate_for_inference(df):
    """(ok, message): can the saved models be applied to this table?"""
    miss = missing_columns(df)
    if miss:
        return False, f"Missing required feature columns: {', '.join(miss)}. Use the output of `python run_module2.py` (route_features.csv) as the template."
    try:
        inf.check_columns(df)
    except ValueError as e:
        return False, str(e)
    bad = [c for c in pp.NUMERIC if c in df and not c.startswith("share_") and not pd.api.types.is_numeric_dtype(df[c])]
    if bad:
        return False, f"These columns must be numeric: {', '.join(bad)}"
    if df.duplicated(["city", "route_id"]).any():
        return False, "Duplicate (city, route_id) pairs found - each route must appear once."
    if (df.n_trips <= 0).any():
        return False, "Some routes have n_trips <= 0; period shares cannot be computed."
    return True, "OK"
