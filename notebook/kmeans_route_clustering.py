
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_DIR / "reports"

CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad",
]

FEATURES = [
    "scheduled_trip_count",
    "scheduled_stop_events",
    "distinct_stops_served",
    "average_stops_per_trip",
]

N_CLUSTERS = 3


def main():
    all_results = []

    for city in CITIES:
        input_file = REPORTS_DIR / f"{city}_route_indicators.csv"

        if not input_file.exists():
            print(f"WARNING: File not found for {city}: {input_file}")
            continue

        df = pd.read_csv(input_file)

        missing_features = [
            feature for feature in FEATURES
            if feature not in df.columns
        ]

        if missing_features:
            print(f"WARNING: {city} is missing: {missing_features}")
            continue

        # Convert model features to numeric values.
        for feature in FEATURES:
            df[feature] = pd.to_numeric(
                df[feature], errors="coerce"
            )

        # Initialize every route as needing review.
        df["cluster"] = -1
        df["cluster_status"] = "Needs review - no scheduled trips"

        # Only cluster routes with at least one scheduled trip.
        active_mask = (
            df["scheduled_trip_count"].notna()
            & (df["scheduled_trip_count"] > 0)
        )

        active = df.loc[active_mask].copy()

        if len(active) < N_CLUSTERS:
            print(
                f"WARNING: Not enough active routes in {city} "
                "for 3 clusters."
            )
            df["city"] = city
            all_results.append(df)
            continue

        # Log-transform count features to reduce extreme-value effects.
        model_data = active[FEATURES].copy()

        count_features = [
            "scheduled_trip_count",
            "scheduled_stop_events",
            "distinct_stops_served",
        ]

        for feature in count_features:
            model_data[feature] = model_data[feature].clip(lower=0)
            model_data[feature] = np.log1p(model_data[feature])

        # Fill missing values, scale features, then run K-Means.
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(
                n_clusters=N_CLUSTERS,
                random_state=42,
                n_init=10,
            )),
        ])

        labels = pipeline.fit_predict(model_data)

        df.loc[active.index, "cluster"] = labels
        df.loc[active.index, "cluster_status"] = "Clustered"

        df["city"] = city
        all_results.append(df)

        print(
            f"{city.title()}: {len(active)} routes clustered; "
            f"{len(df) - len(active)} routes need review."
        )

    if not all_results:
        print("ERROR: No route-indicator files were processed.")
        return

    results = pd.concat(all_results, ignore_index=True)

    output_file = REPORTS_DIR / "kmeans_route_clusters.csv"
    results.to_csv(output_file, index=False)

    # Summarize the route clusters for interpretation.
    clustered = results[results["cluster"] >= 0]

    if not clustered.empty:
        summary = (
            clustered.groupby(["city", "cluster"])
            .agg(
                route_count=("cluster", "size"),
                average_scheduled_trips=(
                    "scheduled_trip_count", "mean"
                ),
                median_scheduled_trips=(
                    "scheduled_trip_count", "median"
                ),
                average_distinct_stops=(
                    "distinct_stops_served", "mean"
                ),
                average_stops_per_trip=(
                    "average_stops_per_trip", "mean"
                ),
            )
            .reset_index()
        )

        summary_file = REPORTS_DIR / "kmeans_cluster_summary.csv"
        summary.to_csv(summary_file, index=False)
        print(f"Cluster summary saved: {summary_file}")

    review_count = (results["cluster"] == -1).sum()

    print(f"Route cluster results saved: {output_file}")
    print(f"Total routes processed: {len(results)}")
    print(f"Routes needing review: {review_count}")


if __name__ == "__main__":
    main()
