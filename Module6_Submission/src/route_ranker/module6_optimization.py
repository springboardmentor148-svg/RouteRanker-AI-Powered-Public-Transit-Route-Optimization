"""Evidence-led route review and a clearly labeled schedule sensitivity scenario."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MODEL_COLUMNS = [
    "kmeans_cluster", "kmeans_distance_to_centroid", "dbscan_cluster",
    "dbscan_is_noise", "dbscan_nearest_core_distance",
]


def _normalize_id(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def _key(frame: pd.DataFrame) -> pd.Series:
    return frame["city"].astype("string").str.strip().str.casefold() + "::" + _normalize_id(frame["route_id"])


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _safe_quantile(values: pd.Series, q: float, fallback: float) -> float:
    clean = values.dropna()
    return float(clean.quantile(q)) if len(clean) else fallback


def load_raw_network(project_root: Path) -> pd.DataFrame:
    # Prefer the selected project folder. Also support the common ROUT layout,
    # where the Module 6 submission is nested under ROUT or the source CSVs sit
    # beside it rather than under data/raw/.
    search_dirs = [
        project_root / "data" / "raw",
        project_root / "Module6_Submission" / "data" / "raw",
        project_root.parent / "data" / "raw",
        project_root.parent,
    ]
    paths: list[Path] = []
    searched: list[str] = []
    seen: set[Path] = set()
    for directory in search_dirs:
        resolved = directory.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        searched.append(str(directory))
        matches = sorted(directory.glob("route_features*.csv")) if directory.is_dir() else []
        if matches:
            paths = matches
            break
    if not paths:
        raise FileNotFoundError(
            "No route_features*.csv files were found for Module 6 network analysis. "
            "Searched: " + "; ".join(searched)
        )
    frames = [pd.read_csv(path, dtype={"city": "string", "route_id": "string", "overlap_partner": "string"}) for path in paths]
    network = pd.concat(frames, ignore_index=True, sort=False)
    required = {"city", "route_id", "n_trips", "length_km", "median_headway_min", "service_span_h", "n_active_hours"}
    missing = sorted(required - set(network.columns))
    if missing:
        raise ValueError(f"Raw route data lacks fields needed for Module 6 analysis: {missing}")
    network["city"] = network["city"].astype("string").str.strip().str.casefold()
    network["route_id"] = _normalize_id(network["route_id"])
    if network.duplicated(["city", "route_id"]).any():
        sample = network.loc[network.duplicated(["city", "route_id"], keep=False), ["city", "route_id"]].head()
        raise ValueError("Duplicate route keys in raw network data:\n" + sample.to_string(index=False))
    return network


def _attach_assignments(network: pd.DataFrame, assignments: pd.DataFrame) -> pd.DataFrame:
    base = network.copy()
    predicted = assignments[["city", "route_id", *MODEL_COLUMNS]].copy()
    base["_route_key"] = _key(base)
    predicted["_route_key"] = _key(predicted)
    joined = base.merge(predicted.drop(columns=["city", "route_id"]), on="_route_key", how="left", validate="one_to_one")
    joined = joined.drop(columns=["_route_key"])
    missing = joined["kmeans_cluster"].isna()
    if missing.any():
        raise ValueError(f"Model assignments are missing for {int(missing.sum())} network routes.")
    return joined


def _make_review_flags(joined: pd.DataFrame) -> pd.DataFrame:
    frame = joined.copy()
    for column in ["n_trips", "median_headway_min", "length_km", "median_trip_duration_min",
                   "n_unique_stops", "max_stop_overlap", "overlap_share_of_route", "kmeans_distance_to_centroid"]:
        frame[column] = _numeric(frame, column)
    frame["dbscan_is_noise"] = frame["dbscan_is_noise"].fillna(False).astype(bool)

    frame["signal_dbscan_noise"] = frame["dbscan_is_noise"]
    frame["signal_kmeans_distance_tail"] = False
    frame["signal_frequency_review"] = False
    frame["signal_long_route_review"] = False
    frame["signal_overlap_review"] = False

    for _, group in frame.groupby("city", dropna=False):
        headway_q75 = _safe_quantile(group["median_headway_min"], 0.75, float("inf"))
        trips_q25 = _safe_quantile(group["n_trips"], 0.25, -float("inf"))
        distance_q95 = _safe_quantile(group["kmeans_distance_to_centroid"], 0.95, float("inf"))
        length_q90 = _safe_quantile(group["length_km"], 0.90, float("inf"))
        duration_q90 = _safe_quantile(group["median_trip_duration_min"], 0.90, float("inf"))
        overlap_q75 = _safe_quantile(group["max_stop_overlap"], 0.75, float("inf"))
        overlap_share_q75 = _safe_quantile(group["overlap_share_of_route"], 0.75, float("inf"))
        index = group.index
        frame.loc[index, "signal_kmeans_distance_tail"] = group["kmeans_distance_to_centroid"] >= distance_q95
        frame.loc[index, "signal_frequency_review"] = (
            (group["median_headway_min"] >= headway_q75)
            & (group["n_trips"] <= trips_q25)
            & group["n_trips"].notna()
            & group["median_headway_min"].notna()
        )
        frame.loc[index, "signal_long_route_review"] = (
            (group["length_km"] >= length_q90)
            & (group["median_trip_duration_min"] >= duration_q90)
            & group["length_km"].notna()
            & group["median_trip_duration_min"].notna()
        )
        frame.loc[index, "signal_overlap_review"] = (
            (group["max_stop_overlap"] >= max(0.70, overlap_q75))
            & (group["overlap_share_of_route"] >= max(0.50, overlap_share_q75))
            & group["max_stop_overlap"].notna()
            & group["overlap_share_of_route"].notna()
        )

    signal_columns = [
        "signal_dbscan_noise", "signal_kmeans_distance_tail", "signal_frequency_review",
        "signal_long_route_review", "signal_overlap_review",
    ]
    frame["review_signal_count"] = frame[signal_columns].sum(axis=1).astype(int)
    reason_labels = {
        "signal_dbscan_noise": "DBSCAN marked the route as low-density noise",
        "signal_kmeans_distance_tail": "K-Means distance is in the city-specific top 5%",
        "signal_frequency_review": "High headway and low scheduled trips versus the same city",
        "signal_long_route_review": "Long distance and long trip duration versus the same city",
        "signal_overlap_review": "High stop-overlap indicators versus the same city",
    }
    frame["review_reasons"] = frame[signal_columns].apply(
        lambda row: "; ".join(reason_labels[column] for column in signal_columns if bool(row[column])), axis=1
    )
    frame["interpretation"] = np.where(
        frame["review_signal_count"] >= 2,
        "Multiple independent screening signals; investigate with operations and passenger data.",
        "Single screening signal only; do not treat as evidence of inefficiency.",
    )
    return frame


def _merge_pairs(network: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "city", "route_a_id", "route_a_name", "route_b_id", "route_b_name",
        "max_stop_overlap", "route_a_overlap_share", "route_b_overlap_share", "review_note",
    ]
    if "overlap_partner" not in network or "max_stop_overlap" not in network:
        return pd.DataFrame(columns=columns)
    frame = network.copy()
    frame["_key"] = _key(frame)
    lookup = frame.set_index("_key", drop=False)
    pair_thresholds: dict[str, tuple[float, float]] = {}
    for city, group in frame.groupby("city", dropna=False):
        overlap_q90 = _safe_quantile(_numeric(group, "max_stop_overlap"), 0.90, 1.0)
        share_q75 = _safe_quantile(_numeric(group, "overlap_share_of_route"), 0.75, 1.0)
        pair_thresholds[str(city)] = (max(0.85, overlap_q90), max(0.75, share_q75))
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    for _, row in frame.iterrows():
        partner_id = str(row.get("overlap_partner", "")).strip()
        if not partner_id or partner_id.casefold() in {"nan", "none", "<na>"}:
            continue
        partner_key = f"{str(row['city']).casefold()}::{_normalize_id(pd.Series([partner_id])).iloc[0]}"
        if partner_key not in lookup.index or partner_key == row["_key"]:
            continue
        partner = lookup.loc[partner_key]
        if isinstance(partner, pd.DataFrame):
            partner = partner.iloc[0]
        a_key, b_key = sorted([str(row["_key"]), partner_key])
        max_overlap = float(pd.to_numeric(pd.Series([row.get("max_stop_overlap"), partner.get("max_stop_overlap")]), errors="coerce").max())
        share_a = float(pd.to_numeric(pd.Series([row.get("overlap_share_of_route")]), errors="coerce").iloc[0])
        share_b = float(pd.to_numeric(pd.Series([partner.get("overlap_share_of_route")]), errors="coerce").iloc[0])
        city_overlap_threshold, city_share_threshold = pair_thresholds.get(str(row["city"]), (0.85, 0.75))
        available_shares = [value for value in (share_a, share_b) if np.isfinite(value)]
        if not np.isfinite(max_overlap) or max_overlap < city_overlap_threshold or not available_shares or max(available_shares) < city_share_threshold:
            continue
        route_a, route_b = (lookup.loc[a_key], lookup.loc[b_key])
        if isinstance(route_a, pd.DataFrame): route_a = route_a.iloc[0]
        if isinstance(route_b, pd.DataFrame): route_b = route_b.iloc[0]
        pairs[(a_key, b_key)] = {
            "city": str(row["city"]),
            "route_a_id": str(route_a["route_id"]),
            "route_a_name": str(route_a.get("route_name", "")),
            "route_b_id": str(route_b["route_id"]),
            "route_b_name": str(route_b.get("route_name", "")),
            "max_stop_overlap": max_overlap,
            "route_a_overlap_share": float(pd.to_numeric(route_a.get("overlap_share_of_route"), errors="coerce")),
            "route_b_overlap_share": float(pd.to_numeric(route_b.get("overlap_share_of_route"), errors="coerce")),
            "review_note": "Pair for planner review only. Shared-stop overlap does not prove that merging preserves coverage or capacity.",
        }
    return pd.DataFrame(list(pairs.values()), columns=columns).sort_values(
        ["max_stop_overlap", "city"], ascending=[False, True], kind="stable"
    ) if pairs else pd.DataFrame(columns=columns)


def _split_candidates(flagged: pd.DataFrame) -> pd.DataFrame:
    columns = ["city", "route_id", "route_name", "length_km", "median_trip_duration_min", "n_unique_stops", "review_note"]
    selected = flagged.loc[flagged["signal_long_route_review"]].copy()
    if selected.empty:
        return pd.DataFrame(columns=columns)
    selected["review_note"] = (
        "Investigate whether a split is operationally useful. Stop sequences, transfer connectivity, "
        "passenger journeys, and route coverage must be checked first."
    )
    return selected[[column for column in columns if column in selected.columns]].sort_values(
        ["city", "length_km"], ascending=[True, False], kind="stable"
    )


def _optimization_suggestions(flagged: pd.DataFrame, merges: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in merges.iterrows():
        rows.append({
            "action_type": "MERGE_OR_COORDINATE_REVIEW",
            "city": row["city"], "route_id": row["route_a_id"], "route_name": row["route_a_name"],
            "related_route_id": row["route_b_id"], "related_route_name": row["route_b_name"],
            "evidence": f"Shared-stop overlap={row['max_stop_overlap']:.3f}; route overlap shares={row['route_a_overlap_share']:.3f},{row['route_b_overlap_share']:.3f}.",
            "proposal": "Review route coordination or a conditional merge only after checking stop coverage, passenger demand, transfers, capacity, and service obligations.",
            "simulation_status": "NOT_SIMULATED_TOPOLOGY_AND_DEMAND_NOT_AVAILABLE",
        })
    for _, row in splits.iterrows():
        rows.append({
            "action_type": "SPLIT_REVIEW",
            "city": row["city"], "route_id": row["route_id"], "route_name": row["route_name"],
            "related_route_id": "", "related_route_name": "",
            "evidence": f"Length={row['length_km']:.2f} km; median trip duration={row['median_trip_duration_min']:.1f} min; city-specific high-tail screen.",
            "proposal": "Review whether a long route should be divided after checking stop sequences, transfers, passenger journeys, and end-to-end coverage.",
            "simulation_status": "NOT_SIMULATED_STOP_SEQUENCE_AND_CONNECTIVITY_NOT_AVAILABLE",
        })
    for _, row in flagged.loc[flagged["signal_frequency_review"]].iterrows():
        rows.append({
            "action_type": "TRIP_FREQUENCY_REVIEW",
            "city": row["city"], "route_id": row["route_id"], "route_name": row.get("route_name", ""),
            "related_route_id": "", "related_route_name": "",
            "evidence": f"Median scheduled headway={row['median_headway_min']:.1f} min and scheduled trips={row['n_trips']:.0f}; both are relative to same-city quartiles.",
            "proposal": "Sensitivity scenario adds one scheduled trip to this route. Confirm demand, minimum service, fleet, and operating constraints before considering an actual timetable change.",
            "simulation_status": "SIMULATED_ONE_ADDITIONAL_SCHEDULED_TRIP",
        })
    columns = ["action_type", "city", "route_id", "route_name", "related_route_id", "related_route_name", "evidence", "proposal", "simulation_status"]
    return pd.DataFrame(rows, columns=columns)


def _network_metric_rows(current: pd.DataFrame, simulated: pd.DataFrame, frequency_adjusted: int) -> pd.DataFrame:
    def measure(frame: pd.DataFrame) -> dict[str, float]:
        trip_column = "simulated_n_trips" if "simulated_n_trips" in frame.columns else "n_trips"
        trips = _numeric(frame, trip_column).fillna(0.0)
        length = _numeric(frame, "length_km")
        active = _numeric(frame, "n_active_hours").clip(lower=0)
        total_active = float(active.fillna(0).sum())
        return {
            "route_count": float(len(frame)),
            "total_scheduled_trips": float(trips.sum()),
            "sum_route_length_km": float(length.sum(min_count=1)) if length.notna().any() else float("nan"),
            "mean_route_length_km": float(length.mean()) if length.notna().any() else float("nan"),
            "mean_scheduled_trips_per_route": float(trips.mean()) if len(trips) else float("nan"),
            "scheduled_trips_per_route_active_hour": float(trips.sum() / total_active) if total_active > 0 else float("nan"),
            "mean_unique_stops_per_route": float(_numeric(frame, "n_unique_stops").mean()),
        }
    current_values = measure(current)
    simulated_values = measure(simulated)
    current_values["frequency_adjusted_routes"] = 0.0
    simulated_values["frequency_adjusted_routes"] = float(frequency_adjusted)
    definitions = {
        "route_count": ("routes", "Number of route records."),
        "total_scheduled_trips": ("scheduled trip records", "Sum of n_trips from the supplied schedule feature data; not passenger boardings."),
        "sum_route_length_km": ("route-km", "Sum of route length_km across routes; not passenger-km or unique network coverage."),
        "mean_route_length_km": ("km/route", "Mean estimated route length for records with a length value."),
        "mean_scheduled_trips_per_route": ("trips/route", "Mean scheduled trips per route record."),
        "scheduled_trips_per_route_active_hour": ("trips/route-active-hour", "Total scheduled trips divided by summed active hours across route records."),
        "mean_unique_stops_per_route": ("stops/route", "Mean route-level unique stop count; a stop shared across routes is counted once per route."),
        "frequency_adjusted_routes": ("routes", "Number of routes with one extra scheduled trip in the sensitivity scenario."),
    }
    records = []
    for metric, current_value in current_values.items():
        simulated_value = simulated_values[metric]
        unit, definition = definitions[metric]
        records.append({
            "metric": metric,
            "current_value": current_value,
            "simulated_value": simulated_value,
            "delta": simulated_value - current_value,
            "unit": unit,
            "definition": definition,
            "scenario": "Frequency sensitivity only: add one scheduled trip to same-city high-headway/low-trip routes; no merges or splits are assumed.",
        })
    return pd.DataFrame(records)


def write_cluster_visualization(assignments: pd.DataFrame, path: Path) -> None:
    counts: list[tuple[str, str, int]] = []
    for algorithm, column in [("K-Means", "kmeans_cluster"), ("DBSCAN", "dbscan_cluster")]:
        for label, count in assignments[column].value_counts().sort_index().items():
            label_name = "Noise" if int(label) == -1 else f"Cluster {int(label)}"
            counts.append((algorithm, label_name, int(count)))
    width, row_height = 820, 34
    height = 96 + row_height * len(counts)
    max_count = max((item[2] for item in counts), default=1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<text x="24" y="34" font-family="Arial" font-size="22" font-weight="700" fill="#16324f">Held-out route inference cluster counts</text>',
             '<text x="24" y="60" font-family="Arial" font-size="13" fill="#475569">Assignments for the unseen validation records</text>']
    y = 92
    colors = {"K-Means": "#1976a5", "DBSCAN": "#e07a32"}
    for algorithm, label, count in counts:
        bar_width = max(2, int(470 * count / max_count))
        parts.append(f'<text x="24" y="{y+16}" font-family="Arial" font-size="13" fill="#334155">{html.escape(algorithm)} · {html.escape(label)}</text>')
        parts.append(f'<rect x="270" y="{y}" width="{bar_width}" height="22" rx="5" fill="{colors[algorithm]}"/>')
        parts.append(f'<text x="{282+bar_width}" y="{y+16}" font-family="Arial" font-size="13" fill="#334155">{count:,}</text>')
        y += row_height
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def write_scenario_visualization(metrics: pd.DataFrame, path: Path) -> None:
    keys = ["route_count", "total_scheduled_trips", "sum_route_length_km"]
    display_names = {"route_count": "Routes", "total_scheduled_trips": "Scheduled trips", "sum_route_length_km": "Sum route length"}
    records = metrics.set_index("metric")
    width, height = 850, 300
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<text x="24" y="34" font-family="Arial" font-size="21" font-weight="700" fill="#16324f">Current network vs frequency sensitivity</text>',
             '<text x="24" y="58" font-family="Arial" font-size="12" fill="#475569">Bars are normalized to each metric current value = 100; exact values are in current_vs_simulated_network_metrics.csv.</text>']
    chart_x, chart_y, chart_w = 260, 82, 320
    for idx, key in enumerate(keys):
        row = records.loc[key]
        current = float(row["current_value"])
        simulated = float(row["simulated_value"])
        ratio = (simulated / current) if current else 1.0
        y = chart_y + idx * 65
        parts.append(f'<text x="24" y="{y+22}" font-family="Arial" font-size="14" fill="#334155">{html.escape(display_names[key])}</text>')
        parts.append(f'<rect x="{chart_x}" y="{y}" width="{chart_w}" height="18" rx="4" fill="#176b87"/>')
        parts.append(f'<rect x="{chart_x}" y="{y+23}" width="{max(2,int(chart_w*ratio))}" height="18" rx="4" fill="#db6b35"/>')
        parts.append(f'<text x="{chart_x+chart_w+14}" y="{y+14}" font-family="Arial" font-size="12" fill="#334155">Current: {current:,.2f}</text>')
        parts.append(f'<text x="{chart_x+chart_w+14}" y="{y+37}" font-family="Arial" font-size="12" fill="#334155">Scenario: {simulated:,.2f}</text>')
    parts.extend([
        '<rect x="24" y="276" width="14" height="14" fill="#176b87"/><text x="44" y="288" font-family="Arial" font-size="12" fill="#334155">Current</text>',
        '<rect x="112" y="276" width="14" height="14" fill="#db6b35"/><text x="132" y="288" font-family="Arial" font-size="12" fill="#334155">Simulated sensitivity</text>',
        "</svg>",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def analyze_network(project_root: Path, raw_network: pd.DataFrame, network_assignments: pd.DataFrame) -> dict[str, Any]:
    results_dir = project_root / "results"
    simulation_dir = project_root / "data" / "simulation"
    visualization_dir = project_root / "visualizations"
    results_dir.mkdir(parents=True, exist_ok=True)
    simulation_dir.mkdir(parents=True, exist_ok=True)

    joined = _attach_assignments(raw_network, network_assignments)
    flagged = _make_review_flags(joined)
    merges = _merge_pairs(raw_network)
    splits = _split_candidates(flagged)
    frequency = flagged.loc[flagged["signal_frequency_review"]].copy()

    display_columns = [
        "city", "route_id", "route_name", "split", "kmeans_cluster", "kmeans_distance_to_centroid",
        "dbscan_cluster", "dbscan_is_noise", "dbscan_nearest_core_distance", "n_trips",
        "median_headway_min", "length_km", "median_trip_duration_min", "max_stop_overlap",
        "overlap_share_of_route", "review_signal_count", "review_reasons", "interpretation",
    ]
    review = flagged.loc[flagged["review_signal_count"] > 0].copy()
    review = review.sort_values(["review_signal_count", "dbscan_is_noise", "kmeans_distance_to_centroid"], ascending=[False, False, False], kind="stable")
    review[[c for c in display_columns if c in review]].to_csv(results_dir / "potential_route_review.csv", index=False)
    merges.to_csv(results_dir / "merge_review_candidates.csv", index=False)
    splits.to_csv(results_dir / "split_review_candidates.csv", index=False)

    suggestions = _optimization_suggestions(flagged, merges, splits)
    suggestions.to_csv(results_dir / "optimization_suggestions.csv", index=False)

    simulated = raw_network.copy()
    simulated["n_trips"] = _numeric(simulated, "n_trips")
    simulated["n_active_hours"] = _numeric(simulated, "n_active_hours")
    frequency_keys = set(_key(frequency))
    simulated["scenario_trip_delta"] = _key(simulated).isin(frequency_keys).astype(int)
    simulated["simulated_n_trips"] = simulated["n_trips"] + simulated["scenario_trip_delta"]
    simulated["simulated_trips_per_active_hour"] = np.where(
        simulated["n_active_hours"] > 0,
        simulated["simulated_n_trips"] / simulated["n_active_hours"],
        np.nan,
    )
    simulated["scenario_name"] = "frequency_sensitivity_plus_one_scheduled_trip_for_review_routes"
    simulated.to_csv(simulation_dir / "simulated_network_frequency_scenario.csv", index=False)
    metrics = _network_metric_rows(raw_network, simulated, int(simulated["scenario_trip_delta"].sum()))
    metrics.to_csv(results_dir / "current_vs_simulated_network_metrics.csv", index=False)

    write_cluster_visualization(
        network_assignments.loc[network_assignments.get("split", pd.Series("", index=network_assignments.index)).astype(str).eq("validation")],
        visualization_dir / "module6_holdout_cluster_counts.svg",
    )
    write_scenario_visualization(metrics, visualization_dir / "module6_network_scenario_comparison.svg")

    return {
        "network_route_count": int(len(raw_network)),
        "review_candidate_count": int(len(review)),
        "routes_with_multiple_review_signals": int((review["review_signal_count"] >= 2).sum()),
        "merge_review_pair_count": int(len(merges)),
        "split_review_route_count": int(len(splits)),
        "frequency_review_route_count": int(len(frequency)),
        "frequency_sensitivity_trip_additions": int(simulated["scenario_trip_delta"].sum()),
        "merge_split_scenarios": "Not simulated; available aggregate overlap/length fields are insufficient to preserve passenger coverage and connectivity.",
    }
