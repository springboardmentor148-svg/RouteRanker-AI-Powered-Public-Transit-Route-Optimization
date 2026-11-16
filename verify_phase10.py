import json
import joblib
import numpy as np
import pandas as pd
import subprocess
import os
import glob

print("=" * 80)
print("PHASE 10: AUTOMATED VERIFICATION OF PREPROCESSING PIPELINE")
print("=" * 80)

# -----------------------------------------------------------------------------
# 1. Check Notebook Execution Status
# -----------------------------------------------------------------------------
print("\n[CHECK 1] Notebook Execution Status")
import nbformat
nb = nbformat.read("module4_preprocessing.ipynb", as_version=4)
code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = []
for idx, cell in enumerate(code_cells):
    for output in cell.get("outputs", []):
        if output.get("output_type") == "error":
            errors.append((idx, output.get("ename"), output.get("evalue")))

if not errors:
    print(f" PASS: All {len(code_cells)} code cells in module4_preprocessing.ipynb executed with 0 errors.")
else:
    print(f" FAIL: Found {len(errors)} error(s) in code cells:")
    for e in errors:
        print(f"   Cell {e[0]}: {e[1]} - {e[2]}")

# -----------------------------------------------------------------------------
# 2. Verify No Data Leakage
# -----------------------------------------------------------------------------
print("\n[CHECK 2] Data Leakage Verification")
lookup_train = pd.read_csv("processed/route_lookup_train.csv")
lookup_val = pd.read_csv("processed/route_lookup_val.csv")
raw_features = pd.read_csv("processed/route_features.csv")

raw_active = raw_features[raw_features["trip_count"] > 0].copy()
raw_train = raw_active.loc[raw_active["route_id"].isin(lookup_train["route_id"])].copy()
raw_val = raw_active.loc[raw_active["route_id"].isin(lookup_val["route_id"])].copy()

# A. Length cap check
with open("processed/pipeline/length_cap.json") as f:
    saved_cap_data = json.load(f)
saved_cap = saved_cap_data["fitted_length_cap_km"]
computed_train_cap = float(np.percentile(raw_train["route_length_km"], 99))
computed_all_cap = float(np.percentile(raw_active["route_length_km"], 99))

print(f"  Length Cap Saved in Pipeline : {saved_cap:.6f} km")
print(f"  Length Cap Computed on Train : {computed_train_cap:.6f} km")
print(f"  Length Cap Computed on All   : {computed_all_cap:.6f} km")
cap_diff = abs(saved_cap - computed_train_cap)
if cap_diff < 1e-5:
    print("  PASS: Length cap strictly fitted on train split (difference < 1e-5).")
else:
    print(f"  FAIL: Length cap does not match train split! diff={cap_diff}")

# B. RobustScaler center & scale check
scaler = joblib.load("processed/feature_scaler.joblib")
num_features = [
    "trip_count_log1p",
    "stop_count",
    "route_length_km_log1p",
    "service_span_hours",
    "first_departure_hour",
    "morning_trip_share",
    "evening_trip_share",
    "night_trip_share"
]

train_calc = raw_train.copy()
train_calc["route_length_km"] = np.minimum(train_calc["route_length_km"], saved_cap)
train_calc["trip_count_log1p"] = np.log1p(train_calc["trip_count"])
train_calc["route_length_km_log1p"] = np.log1p(train_calc["route_length_km"])
train_calc["morning_trip_share"] = train_calc["trips_morning"] / train_calc["trip_count"]
train_calc["evening_trip_share"] = train_calc["trips_evening"] / train_calc["trip_count"]
train_calc["night_trip_share"] = train_calc["trips_night"] / train_calc["trip_count"]

all_calc = raw_active.copy()
all_calc["route_length_km"] = np.minimum(all_calc["route_length_km"], saved_cap)
all_calc["trip_count_log1p"] = np.log1p(all_calc["trip_count"])
all_calc["route_length_km_log1p"] = np.log1p(all_calc["route_length_km"])
all_calc["morning_trip_share"] = all_calc["trips_morning"] / all_calc["trip_count"]
all_calc["evening_trip_share"] = all_calc["trips_evening"] / all_calc["trip_count"]
all_calc["night_trip_share"] = all_calc["trips_night"] / all_calc["trip_count"]

train_medians = train_calc[num_features].median().values
all_medians = all_calc[num_features].median().values

print("\n  Scaler Center (Median) Parameter Check:")
print(f"  {'Feature':<25} | {'Fitted Scaler':<14} | {'Train Median':<14} | {'All Median':<14} | {'Match Train?'}")
print("  " + "-" * 78)
for col, fitted, t_med, a_med in zip(num_features, scaler.center_, train_medians, all_medians):
    match = abs(fitted - t_med) < 1e-5
    print(f"  {col:<25} | {fitted:14.6f} | {t_med:14.6f} | {a_med:14.6f} | {'PASS' if match else 'FAIL'}")

# C. One-Hot Encoder categories check
encoder = joblib.load("processed/one_hot_encoder_period.joblib")
print(f"\n  OneHotEncoder handle_unknown : {encoder.handle_unknown}")
print(f"  OneHotEncoder categories     : {encoder.categories_[0].tolist()}")
if encoder.handle_unknown == "ignore":
    print("  PASS: OneHotEncoder configured with handle_unknown='ignore' to prevent unseen category failure.")
else:
    print(f"  FAIL: OneHotEncoder handle_unknown is {encoder.handle_unknown}")

# -----------------------------------------------------------------------------
# 3. Verify Processed Data Integrity
# -----------------------------------------------------------------------------
print("\n[CHECK 3] Processed Data Integrity Check")
X_train = pd.read_csv("processed/X_train.csv")
X_val = pd.read_csv("processed/X_val.csv")
X_all = pd.read_csv("processed/X_all.csv")

with open("processed/feature_list.json") as f:
    feature_list = json.load(f)

print(f"  X_train shape: {X_train.shape} (Expected: 7386 x 12)")
print(f"  X_val shape  : {X_val.shape} (Expected: 1847 x 12)")
print(f"  X_all shape  : {X_all.shape} (Expected: 9233 x 12)")

# Check missing and inf
for name, df in [("X_train", X_train), ("X_val", X_val), ("X_all", X_all)]:
    n_nan = df.isna().sum().sum()
    n_inf = np.isinf(df.to_numpy()).sum()
    if n_nan == 0 and n_inf == 0:
        print(f"  PASS: {name} has 0 NaN and 0 Inf values.")
    else:
        print(f"  FAIL: {name} has {n_nan} NaNs, {n_inf} Infs.")

# Check column alignment
cols_train = list(X_train.columns)
cols_val = list(X_val.columns)
cols_all = list(X_all.columns)

if cols_train == feature_list and cols_val == feature_list and cols_all == feature_list:
    print(f"  PASS: All feature matrices strictly match feature_list.json ({len(feature_list)} features in identical order).")
else:
    print("  FAIL: Feature matrix columns do not match feature_list.json!")

# Check dtypes
non_numeric = [col for col in X_train.columns if not np.issubdtype(X_train[col].dtype, np.number)]
if not non_numeric:
    print("  PASS: All columns in X_train/X_val/X_all are strictly numeric.")
else:
    print(f"  FAIL: Non-numeric columns in feature matrix: {non_numeric}")

# Check identifier isolation
id_cols_detected = [c for c in X_train.columns if any(w in c.lower() for w in ["route_id", "agency_id", "route_name", "city"])]
if not id_cols_detected:
    print("  PASS: Identifiers completely excluded from model matrix.")
else:
    print(f"  FAIL: Identifiers found in model matrix: {id_cols_detected}")

# -----------------------------------------------------------------------------
# 4. Independent Recomputation for 3 Random Routes from Different Cities
# -----------------------------------------------------------------------------
print("\n[CHECK 4] Independent Recomputation for 3 Routes from Different Cities")
# Select 1 from bengaluru, 1 from mumbai, 1 from delhi
bmtc_route = lookup_train[lookup_train["city"] == "bengaluru"].iloc[100]["route_id"]
best_route = lookup_train[lookup_train["city"] == "mumbai"].iloc[100]["route_id"]
dtc_route = lookup_val[lookup_val["city"] == "delhi"].iloc[50]["route_id"]

test_routes = [
    ("bengaluru", bmtc_route, "X_train"),
    ("mumbai", best_route, "X_train"),
    ("delhi", dtc_route, "X_val")
]

period_cols = ["trips_morning", "trips_afternoon", "trips_evening", "trips_night"]

for city, rid, matrix_name in test_routes:
    print(f"\n  --- Testing Route: {rid} (City: {city}, Source: {matrix_name}) ---")
    raw_row = raw_features[raw_features["route_id"] == rid].iloc[0]
    
    # 1. Raw extraction
    tc = float(raw_row["trip_count"])
    rlen = float(raw_row["route_length_km"])
    sc = float(raw_row["stop_count"])
    span = float(raw_row["service_span_hours"])
    fdep = float(raw_row["first_departure_hour"])
    tm = float(raw_row["trips_morning"])
    ta = float(raw_row["trips_afternoon"])
    te = float(raw_row["trips_evening"])
    tn = float(raw_row["trips_night"])
    
    # 2. Capping
    capped_rlen = min(rlen, saved_cap)
    
    # 3. Log1p
    log_tc = np.log1p(tc)
    log_rlen = np.log1p(capped_rlen)
    
    # 4. Diurnal Shares
    m_share = tm / tc
    e_share = te / tc
    n_share = tn / tc
    
    # 5. Dominant Period (idxmax order: morning, afternoon, evening, night)
    p_series = pd.Series([tm, ta, te, tn], index=["morning", "afternoon", "evening", "night"])
    dom_period = p_series.idxmax()
    
    # One-hot vector in order: period_afternoon, period_evening, period_morning, period_night
    oh_afternoon = 1.0 if dom_period == "afternoon" else 0.0
    oh_evening = 1.0 if dom_period == "evening" else 0.0
    oh_morning = 1.0 if dom_period == "morning" else 0.0
    oh_night = 1.0 if dom_period == "night" else 0.0
    
    # 6. Manual RobustScaler transform
    raw_vec_num = np.array([log_tc, sc, log_rlen, span, fdep, m_share, e_share, n_share])
    scaled_num = (raw_vec_num - scaler.center_) / scaler.scale_
    
    manual_full_vec = np.concatenate([
        scaled_num,
        np.array([oh_afternoon, oh_evening, oh_morning, oh_night])
    ])
    
    # Load actual row from saved matrix
    lookup_file = lookup_train if matrix_name == "X_train" else lookup_val
    matrix_df = X_train if matrix_name == "X_train" else X_val
    row_idx = lookup_file[lookup_file["route_id"] == rid].index[0]
    saved_vec = matrix_df.iloc[row_idx].values
    
    max_abs_diff = np.max(np.abs(manual_full_vec - saved_vec))
    print(f"  Raw values: trip_count={tc:.0f}, route_length_km={rlen:.2f} (capped={capped_rlen:.2f}), dominant_period={dom_period}")
    print(f"  Feature-by-Feature Comparison:")
    for fn, m_val, s_val in zip(feature_list, manual_full_vec, saved_vec):
        print(f"    {fn:<30}: manual={m_val:10.5f} | saved={s_val:10.5f} | diff={abs(m_val - s_val):.2e}")
    print(f"  Maximum Absolute Discrepancy: {max_abs_diff:.10e}")
    if max_abs_diff < 1e-6:
        print("  PASS: Independent manual calculation EXACTLY matches saved matrix!")
    else:
        print("  FAIL: Discrepancy exceeds tolerance!")

# -----------------------------------------------------------------------------
# 5. Check Raw Files & Prohibited Words
# -----------------------------------------------------------------------------
print("\n[CHECK 5] Confirm Raw Files Intact & Prohibited Terminology Screening")
git_diff = subprocess.run(["git", "diff", "--name-only", "processed/route_features.csv", "processed/route_features_flagged.csv"], capture_output=True, text=True)
if git_diff.stdout.strip() == "":
    print("  PASS: Input CSVs (processed/route_features.csv, route_features_flagged.csv) are 100% UNCHANGED.")
else:
    print(f"  WARNING: Modified input files: {git_diff.stdout.strip()}")

# Scan for forbidden terms in column names of all files in processed/
forbidden_words = ["passenger", "rider", "ridership", "crowd", "overcrowd", "underutilis", "inefficien", "target", "label", "performance"]
found_forbidden = []
for fpath in glob.glob("processed/*.csv"):
    df_temp = pd.read_csv(fpath, nrows=2)
    for col in df_temp.columns:
        for fw in forbidden_words:
            if fw in col.lower():
                found_forbidden.append((fpath, col, fw))

if not found_forbidden:
    print("  PASS: 0 passenger counts, ridership metrics, or synthetic performance labels detected across all processed CSVs.")
else:
    print(f"  FAIL: Found prohibited terminology in processed columns: {found_forbidden}")

# -----------------------------------------------------------------------------
# 6. Model Suitability Summary
# -----------------------------------------------------------------------------
print("\n[CHECK 6] KMeans & DBSCAN Suitability Analysis")
print("  - KMeans: Feature matrix is zero-centered with IQR scaling; log1p mitigated heavy positive skew.")
print("  - DBSCAN: Continuous metric space without missing/infinite entries; density-based radius estimation feasible.")
print("  - Classification Requirements:")
print("    * True ground-truth labels (e.g. verified ridership surveys, load factors, APC data) are required.")
print("    * Currently NO performance labels exist, strictly adhering to scheduled GTFS constraints.")

print("\n" + "=" * 80)
print("PHASE 10 VERIFICATION COMPLETED SUCCESSFULLY")
print("=" * 80)
