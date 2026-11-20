"""Route-optimisation layer of the dashboard (Module 6): live what-if recalculation with the same functions as run_module6.py.
Everything here is a SUGGESTION to verify or a SIMULATED result - never a confirmed improvement."""
import numpy as np
import pandas as pd
import streamlit as st

from src import optimization as opt, preprocessing as pp
from . import data_loader as dl

DEFAULTS = dict(jac_min=opt.MERGE_JACCARD, low_q=opt.MERGE_LOW_Q, len_ratio=opt.MERGE_LEN_RATIO, min_km=opt.SPLIT_MIN_KM, len_q=opt.SPLIT_LEN_Q,
                min_stops=opt.SPLIT_MIN_STOPS, min_trips=opt.FREQ_MIN_TRIPS, standard=opt.FREQ_HEADWAY_STANDARD)
SCENARIOS = ["current network", "merge only", "split only", "frequency standard only", "combined"]
SCEN_KEY = {"merge only": "merge", "split only": "split", "frequency standard only": "frequency", "combined": "combined"}


@st.cache_data(show_spinner=False)
def base_network():
    raw = pp.add_derived(dl.load_routes())
    pred = dl.load_predictions()[["city", "route_id", "kmeans_cluster", "dbscan_label"]]
    b = raw.merge(pred, on=["city", "route_id"], how="left")
    return b[~b.city.isin(dl.EXCLUDED_FEEDS)].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def sparse_clusters():
    prof = dl.load_table("module5_kmeans_cluster_profile.csv")
    return [int(c) for c in prof.loc[prof.n_trips <= 2, "cluster"]]


@st.cache_data(show_spinner="Recalculating suggestions ...")
def candidates(params):
    """params = tuple in DEFAULTS order. Returns (routes with evidence flags, merges, splits, frequency candidates)."""
    p = dict(zip(DEFAULTS, params))
    ev, flags = opt.evidence_flags(base_network(), sparse_clusters(), p["jac_min"])
    mg = opt.merge_candidates(ev, p["jac_min"], p["low_q"], p["len_ratio"])
    sp = opt.split_candidates(ev, (), p["min_km"], p["len_q"], p["min_stops"])
    fq = opt.frequency_candidates(ev, (), p["min_trips"], p["standard"])
    return ev, mg, sp, fq


@st.cache_data(show_spinner="Simulating the scenarios on a copy of the network ...")
def scenario_metrics(params):
    p = dict(zip(DEFAULTS, params))
    ev, mg, sp, fq = candidates(params)
    rows = []
    for name in SCENARIOS:
        df = ev[opt.SIMCOLS].copy() if name == "current network" else opt.simulate(ev, mg, sp, fq, SCEN_KEY[name])
        for city, g in list(df.groupby("city")) + [("ALL CITIES", df)]:
            m = opt.metrics(g, p["min_trips"], p["standard"], p["min_km"])
            if name not in ("current network", "frequency standard only"):
                m["routes_with_under_2_departures_in_peak_hour"] = np.nan      # 'busiest hour' is only well defined for these two
            rows.append(dict(scenario=name, city=city, **m))
    return pd.DataFrame(rows)


def evidence_text(ev):
    flag_names = {"ev_dbscan_noise": "unusual for DBSCAN (noise)", "ev_sparse_cluster": "in a KMeans cluster of very few trips",
                  "ev_high_stop_overlap": "shares most of its stops with another route", "ev_low_trips_for_length": "few trips compared with routes of similar length"}
    return ev[list(flag_names)].apply(lambda r: "; ".join(v for k, v in flag_names.items() if r[k]), axis=1)


def merge_preview(row):
    """What one merge would do to the schedule data (same formulas as the simulation)."""
    keep = 1 - row.share_of_absorbed_stops_also_on_target
    return pd.DataFrame({
        "": ["scheduled trips", "estimated length (km)", "distinct stops (approx.)"],
        f"target route {row.target_route}": [row.trips_target, row.length_target_km, np.nan],
        f"absorbed route {row.absorbed_route}": [row.trips_absorbed, row.length_absorbed_km, row.stops_absorbed],
        "merged route (SIMULATED)": [row.trips_target + row.trips_absorbed, round(row.length_target_km + row.length_absorbed_km * keep, 1), np.nan]})
