"""Small GTFS helpers shared by Module 2 / 3: time parsing, frequency expansion, distances, route geometry, stop overlap.

No ridership or demand logic lives here."""
import numpy as np
import pandas as pd

def gtfs_time_to_sec(s: pd.Series) -> pd.Series:
    """'HH:MM:SS' (HH may be >=24) -> seconds. Invalid -> NaN."""
    parts = s.astype(str).str.strip().str.split(":", expand=True)
    if parts.shape[1] < 2:
        return pd.Series(np.nan, index=s.index)
    h = pd.to_numeric(parts[0], errors="coerce")
    m = pd.to_numeric(parts[1], errors="coerce")
    sec = pd.to_numeric(parts[2], errors="coerce") if parts.shape[1] > 2 else 0
    return h * 3600 + m * 60 + sec


def expand_frequencies(f, rep=None, max_runs=400):
    """Feeds that use frequencies.txt describe 'a bus every N seconds' instead of listing trips.
    Expand each such template trip into explicit trips so trip counts / hourly supply are right."""
    fr = f.get("frequencies")
    if fr is None or fr.empty:
        return f
    fr = fr.copy()
    fr["s"] = gtfs_time_to_sec(fr.start_time)
    fr["e"] = gtfs_time_to_sec(fr.end_time)
    fr["h"] = pd.to_numeric(fr.headway_secs, errors="coerce")
    fr = fr.dropna(subset=["s", "e", "h"])
    fr = fr[(fr.h > 0) & (fr.e > fr.s) & fr.trip_id.isin(f["trips"].trip_id)]
    if fr.empty:
        return f
    fr["n"] = np.minimum(np.ceil((fr.e - fr.s) / fr.h).astype(int), max_runs)
    runs = fr.loc[fr.index.repeat(fr.n), ["trip_id", "s", "h"]].reset_index(drop=True)
    runs["k"] = runs.groupby(["trip_id", "s", "h"]).cumcount()
    runs["new_start"] = runs.s + runs.k * runs.h
    runs["new_id"] = runs.trip_id + "__f" + runs.index.astype(str)

    st, tr = f["stop_times"], f["trips"]
    tpl = st[st.trip_id.isin(fr.trip_id)].copy()
    first = tpl.groupby("trip_id").dep_s.transform("min")
    tpl["off_dep"] = tpl.dep_s - first
    tpl["off_arr"] = tpl.arr_s - first
    keep = ["trip_id", "stop_id", "stop_sequence", "off_dep", "off_arr"]
    ex = runs[["trip_id", "new_id", "new_start"]].merge(tpl[keep], on="trip_id")
    new_st = pd.DataFrame({"trip_id": ex.new_id, "stop_id": ex.stop_id, "stop_sequence": ex.stop_sequence,
                           "dep_s": ex.new_start + ex.off_dep, "arr_s": ex.new_start + ex.off_arr})
    new_tr = runs[["trip_id", "new_id"]].merge(tr, on="trip_id").drop(columns="trip_id").rename(columns={"new_id": "trip_id"})
    f["stop_times"] = pd.concat([st[~st.trip_id.isin(fr.trip_id)], new_st], ignore_index=True)
    f["trips"] = pd.concat([tr[~tr.trip_id.isin(fr.trip_id)], new_tr], ignore_index=True)
    if rep is not None:
        rep["frequency_trips_expanded"] = int(len(runs))
    return f


def haversine(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2) ** 2 +
         np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * np.arcsin(np.sqrt(a))  # km


def route_geometry(feed):
    """Route length (km) from its longest trip + stop sets per route."""
    st = feed["stop_times"].merge(feed["trips"][["trip_id", "route_id"]], on="trip_id") \
        .merge(feed["stops"][["stop_id", "stop_lat", "stop_lon"]], on="stop_id")
    counts = st.groupby(["route_id", "trip_id"]).size().reset_index(name="n")
    rep_trip = counts.sort_values("n").drop_duplicates("route_id", keep="last")
    rt = st.merge(rep_trip[["trip_id"]], on="trip_id").sort_values(["trip_id", "stop_sequence"])
    rt["seg"] = haversine(rt.stop_lat.shift(), rt.stop_lon.shift(), rt.stop_lat, rt.stop_lon)
    rt.loc[rt.trip_id != rt.trip_id.shift(), "seg"] = 0
    length = rt.groupby("route_id").seg.sum().rename("length_km")
    stops_by_route = st.groupby("route_id").stop_id.agg(lambda x: set(x))
    ends = rt.groupby("route_id").stop_id.agg(first="first", last="last")
    return length, stops_by_route, ends.apply(tuple, axis=1).to_dict()


def stop_overlap(stops_by_route, names=None, ends=None):
    """For each route: best overlapping partner and Jaccard / containment."""
    inv = {}
    for r, ss in stops_by_route.items():
        for s in ss:
            inv.setdefault(s, []).append(r)
    rows = []
    for r, ss in stops_by_route.items():
        cnt = {}
        for s in ss:
            for o in inv[s]:
                if o == r or (names is not None and names.get(o) == names.get(r)):
                    continue  # same-name routes = variants of one line
                if ends is not None and r in ends and o in ends and \
                        ends[r][0] == ends[o][1] and ends[r][1] == ends[o][0] and ends[r][0] != ends[r][1]:
                    continue  # opposite direction (Up/Down) of the same line: never a merge candidate
                cnt[o] = cnt.get(o, 0) + 1
        best, bj, bc = None, 0.0, 0.0
        for o, c in sorted(cnt.items()):   # sorted -> deterministic tie-break (smallest route_id wins)
            j = c / (len(ss) + len(stops_by_route[o]) - c)
            if j > bj:
                best, bj, bc = o, j, c / len(ss)
        rows.append((r, best, bj, bc))
    return pd.DataFrame(rows, columns=["route_id", "overlap_partner", "overlap_jaccard",
                                       "overlap_share"]).set_index("route_id")
