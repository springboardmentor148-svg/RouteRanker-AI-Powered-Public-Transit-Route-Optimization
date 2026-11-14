"""Run the clustering workflow and optional labeled classification workflow."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from route_ranker.module5_clustering import run as run_clustering
from route_ranker.module5_supervised import run as run_supervised


def main() -> int:
    parser = argparse.ArgumentParser(description="Train RouteRanker Module 5 models and save all outputs.")
    parser.add_argument("--dataset", type=Path, default=None, help="Optional Module 4 routes_ml_ready.csv path.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional CSV with city, route_id, label columns.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    summary = run_clustering(ROOT, args.dataset, args.seed)
    run_supervised(ROOT, args.labels, args.seed)
    print("Module 5 outputs saved under models/, results/, reports/, and visualizations/.")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
