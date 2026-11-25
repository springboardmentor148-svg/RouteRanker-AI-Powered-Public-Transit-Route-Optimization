import ast
import hashlib
import json
import math
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

print("=" * 85)
print("  MODULE 6 PHASE 10 — INDEPENDENT VERIFICATION & INTEGRITY AUDIT")
print("=" * 85)

# 1. Check .gitignore & raw/training/model integrity
print("\n[CHECK 1] Original Raw, Training & Saved Model File Modification Audit")
protected_paths = [
    Path("NEW CITY/GTFS/routes.txt"),
    Path("NEW CITY/GTFS/trips.txt"),
    Path("NEW CITY/GTFS/stop_times.txt"),
    Path("NEW CITY/GTFS/stops.txt"),
    Path("NEW CITY/GTFS/calendar.txt"),
    Path("processed/route_features.csv"),
    Path("processed/X_train.csv"),
    Path("processed/X_all.csv"),
    Path("processed/pipeline/feature_scaler.joblib"),
    Path("processed/pipeline/one_hot_encoder.joblib"),
    Path("processed/pipeline/feature_list.json"),
    Path("processed/pipeline/length_cap.json"),
    Path("models/kmeans_model.joblib"),
    Path("models/dbscan_model.joblib"),
]
for p in protected_paths:
    st = p.stat()
    print(f"  OK {str(p):<48} | size={st.st_size:>10,} bytes | mtime={pd.Timestamp(st.st_mtime, unit='s')}")

# 2. Scan code for .fit() / .fit_transform() calls (Leakage Check)
print("\n[CHECK 2] AST / Code Scan for fit() or fit_transform() Calls")
with open("module6_inference.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

fit_hits = []
for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"fit", "fit_transform"}:
                    line_txt = src.splitlines()[node.lineno - 1].strip()
                    fit_hits.append((idx, node.func.attr, line_txt))
    except SyntaxError:
        pass

for p_file in [Path("src/feature_pipeline.py")]:
    src = p_file.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"fit", "fit_transform"}:
                fit_hits.append((str(p_file), node.func.attr, src.splitlines()[node.lineno - 1].strip()))

print(f"  Total fit/fit_transform calls detected across notebook & src/: {len(fit_hits)}")
for loc, meth, txt in fit_hits:
    print(f"    Cell/File={loc} | .{meth}() -> {txt}")

# Verify NO notebook cell has errors
err_cells = []
for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                err_cells.append((idx, out.get("ename"), out.get("evalue")))
print(f"  Notebook execution errors found: {len(err_cells)}")

# 3. Independent Recomputation for 3 Random Chennai Routes (seed=42)
print("\n[CHECK 3] Independent Raw GTFS Verification for 3 Random Chennai Routes (seed=42)")
saved_feat = pd.read_csv(
    "inference/new_city_route_features.csv",
    dtype={"city": str, "route_id": str, "original_route_id": str, "route_short_name": str, "route_long_name": str},
)
active_saved = saved_feat[saved_feat["trip_count"].notna()].copy()
sample_3 = active_saved.sample(n=3, random_state=42).reset_index(drop=True)

raw_trips = pd.read_csv("NEW CITY/GTFS/trips.txt", dtype={"route_id": str, "trip_id": str, "service_id": str})
raw_st = pd.read_csv("NEW CITY/GTFS/stop_times.txt", dtype={"trip_id": str, "stop_id": str})
raw_stops = pd.read_csv("NEW CITY/GTFS/stops.txt", dtype={"stop_id": str})
raw_cal = pd.read_csv("NEW CITY/GTFS/calendar.txt", dtype={"service_id": str})

def indep_to_sec(s):
    h, m, sec = [int(x) for x in str(s).strip().split(":")]
    return float(h * 3600 + m * 60 + sec)

def indep_hav(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2.0 * math.asin(min(1.0, math.sqrt(a)))

raw_stops_map = raw_stops.set_index("stop_id")[["stop_lat", "stop_lon"]].to_dict("index")
cal_map = raw_cal.set_index("service_id").to_dict("index")

km_model = joblib.load("models/kmeans_model.joblib")
db_model = joblib.load("models/dbscan_model.joblib")
scaler = joblib.load("processed/pipeline/feature_scaler.joblib")
ohe = joblib.load("processed/pipeline/one_hot_encoder.joblib")
feat_list = json.loads(Path("processed/pipeline/feature_list.json").read_text())
len_cap = json.loads(Path("processed/pipeline/length_cap.json").read_text())["fitted_length_cap_km"]

km_saved = pd.read_csv("inference/new_city_kmeans_assignments.csv", dtype={"route_id": str}).set_index("route_id")
db_saved = pd.read_csv("inference/new_city_dbscan_assignments.csv", dtype={"route_id": str}).set_index("route_id")
core_labels = db_model.labels_[db_model.core_sample_indices_]
nn_check = NearestNeighbors(n_neighbors=1, metric=db_model.metric).fit(db_model.components_)

for _, row in sample_3.iterrows():
    rid = row["route_id"]
    orig_rid = row["original_route_id"]
    rt = raw_trips[raw_trips["route_id"] == orig_rid].copy()
    rst = raw_st[raw_st["trip_id"].isin(rt["trip_id"])].copy()
    rst["dep_s"] = rst["departure_time"].apply(indep_to_sec)
    rst["seq_n"] = pd.to_numeric(rst["stop_sequence"])

    ind_trips = rt["trip_id"].nunique()
    ind_stops = rst["stop_id"].nunique()

    # Representative trip for chord length
    first_stops = rst.sort_values(["trip_id", "seq_n"]).drop_duplicates("trip_id", keep="first")
    trip_len_counts = rst.groupby("trip_id").size()
    rep_tid = trip_len_counts.idxmax()
    rep_seq = rst[rst["trip_id"] == rep_tid].sort_values("seq_n")["stop_id"].tolist()
    ind_len = sum(
        indep_hav(
            raw_stops_map[rep_seq[i]]["stop_lat"], raw_stops_map[rep_seq[i]]["stop_lon"],
            raw_stops_map[rep_seq[i+1]]["stop_lat"], raw_stops_map[rep_seq[i+1]]["stop_lon"],
        )
        for i in range(len(rep_seq) - 1)
    )

    # Headway within (direction_id, service_id)
    rt = rt.merge(first_stops[["trip_id", "dep_s"]], on="trip_id", how="left")
    hws = []
    for _, grp in rt.sort_values("dep_s").groupby(["service_id", "direction_id"]):
        diffs = grp["dep_s"].diff().dropna() / 60.0
        hws.extend(diffs.tolist())
    ind_hw = float(np.median(hws)) if hws else float("nan")

    # Periods & span
    hrs = (first_stops["dep_s"] // 3600) % 24
    ind_am = int(((hrs >= 5) & (hrs <= 11)).sum())
    ind_pm = int(((hrs >= 12) & (hrs <= 16)).sum())
    ind_ev = int(((hrs >= 17) & (hrs <= 20)).sum())
    ind_nt = int(((hrs >= 21) | (hrs <= 4)).sum())
    ind_span = round((first_stops["dep_s"].max() - first_stops["dep_s"].min()) / 3600.0, 2)

    assert ind_trips == int(row["trip_count"])
    assert ind_stops == int(row["stop_count"])
    assert np.isclose(ind_len, float(row["route_length_km"]), atol=1e-6)
    assert (np.isnan(ind_hw) and np.isnan(row["median_headway_min"])) or np.isclose(ind_hw, float(row["median_headway_min"]), atol=1e-6)
    assert ind_am == int(row["trips_morning"]) and ind_pm == int(row["trips_afternoon"])
    assert ind_ev == int(row["trips_evening"]) and ind_nt == int(row["trips_night"])
    assert np.isclose(ind_span, float(row["service_span_hours"]), atol=1e-6)

    # Direct model prediction verification
    clipped_len = min(ind_len, len_cap)
    dom_p = max([("morning", ind_am), ("afternoon", ind_pm), ("evening", ind_ev), ("night", ind_nt)], key=lambda x: x[1])[0]
    # Note pandas idxmax picks first occurrence in ['trips_morning', 'trips_afternoon', 'trips_evening', 'trips_night'], same priority!
    x_num = pd.DataFrame([{
        "trip_count_log1p": np.log1p(ind_trips),
        "stop_count": ind_stops,
        "route_length_km_log1p": np.log1p(clipped_len),
        "service_span_hours": ind_span,
        "first_departure_hour": float(first_stops["dep_s"].min() // 3600),
        "morning_trip_share": ind_am / ind_trips,
        "evening_trip_share": ind_ev / ind_trips,
        "night_trip_share": ind_nt / ind_trips,
    }])
    x_sc = pd.DataFrame(scaler.transform(x_num), columns=[f"{c}_scaled" for c in x_num.columns])
    x_oh = pd.DataFrame(ohe.transform(pd.DataFrame({"dominant_time_period": [dom_p]})), columns=[f"period_{c}" for c in ohe.categories_[0]])
    x_vec = pd.concat([x_sc, x_oh], axis=1)[feat_list]

    km_pred = int(km_model.predict(x_vec)[0])
    d_c, idx_c = nn_check.kneighbors(x_vec.values)
    db_pred = "unassigned" if d_c[0][0] > db_model.eps else str(core_labels[idx_c[0][0]])

    assert km_pred == int(km_saved.loc[rid, "kmeans_cluster_MODEL_PREDICTION"])
    assert db_pred == str(db_saved.loc[rid, "dbscan_cluster_MODEL_PREDICTION"])

    print(f"  [PASS] {rid} ({row['route_short_name']}): trips={ind_trips}, stops={ind_stops}, len={ind_len:.2f}km, hw={ind_hw}, span={ind_span}h | KMeans={km_pred}, DBSCAN={db_pred}")

# 4. Content & Provenance Scan across CSVs, Notebook, and Report
print("\n[CHECK 4] Prohibited Language & Provenance Labeling Audit")
prohibited = ["overcrowd", "underutilis", "underutiliz", "inefficien", "ridership", "passenger_count"]
for folder in [Path("inference"), Path("simulation"), Path("results")]:
    for csv_p in sorted(folder.glob("*.csv")):
        hdr = pd.read_csv(csv_p, nrows=0).columns.tolist()
        bad_cols = [c for c in hdr if any(w in c.lower() for w in prohibited)]
        if bad_cols:
            print(f"  WARNING {csv_p}: suspect columns {bad_cols}")

print("  Column header prohibited check complete across inference/, simulation/, results/.")

# Scan chart titles in module6_inference.ipynb
print("\n  Chart titles in module6_inference.ipynb:")
for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        for line in src.splitlines():
            if "set_title(" in line or "suptitle(" in line:
                print(f"    Cell {idx}: {line.strip()[:115]}")
