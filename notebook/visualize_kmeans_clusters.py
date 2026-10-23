
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_DIR / "reports"

INPUT_FILE = REPORTS_DIR / "kmeans_route_clusters.csv"
OUTPUT_FILE = REPORTS_DIR / "kmeans_cluster_distribution.png"


def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: File not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    required_columns = {"city", "cluster"}
    if not required_columns.issubset(df.columns):
        print("ERROR: Input file must contain city and cluster columns.")
        return

    # Exclude cluster -1 because these routes need review.
    clustered = df[df["cluster"] >= 0].copy()

    if clustered.empty:
        print("ERROR: No clustered routes found.")
        return

    counts = (
        clustered.groupby(["city", "cluster"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    ax = counts.plot(
        kind="bar",
        figsize=(10, 6),
        width=0.8
    )

    ax.set_title("K-Means Route Cluster Distribution by City")
    ax.set_xlabel("City")
    ax.set_ylabel("Number of Routes")
    ax.legend(title="Cluster")
    ax.tick_params(axis="x", rotation=0)

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Chart saved successfully: {OUTPUT_FILE}")
    print("\nRoute counts used in the chart:")
    print(counts.to_string())


if __name__ == "__main__":
    main()

