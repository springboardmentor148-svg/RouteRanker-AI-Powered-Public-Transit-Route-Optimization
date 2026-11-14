"""Run RouteRanker Module 6 inference and route-optimization analysis."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Module6_Submission" / "src"))
from route_ranker.module6_workflow import discover_project_root, run_module6


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Module 6 inference on saved Module 5 models.")
    parser.add_argument("--project-root", type=Path, default=discover_project_root(ROOT), help="Module 6 project folder.")
    parser.add_argument("--unseen-data", type=Path, default=None, help="Optional raw or Module 4 prepared route CSV.")
    args = parser.parse_args()
    project_root = args.project_root.expanduser().resolve()
    unseen_data = args.unseen_data.expanduser() if args.unseen_data else None
    if unseen_data is not None and not unseen_data.is_absolute():
        unseen_data = project_root / unseen_data
    summary = run_module6(project_root, unseen_data)
    print("\nROUTERANKER MODULE 6 COMPLETED")
    print(f"Unseen route rows:              {summary['unseen_inference']['input_rows']:,}")
    print(f"K-Means selected K:             {summary['unseen_inference']['selected_kmeans_k']}")
    print(f"DBSCAN cluster counts:          {summary['unseen_inference']['dbscan_cluster_counts_including_noise']}")
    print(f"DBSCAN noise share:              {summary['unseen_inference']['dbscan_noise_share']:.2%}")
    print(f"Potential review candidates:     {summary['network_analysis']['review_candidate_count']:,}")
    print(f"Merge pairs for manual review:   {summary['network_analysis']['merge_review_pair_count']:,}")
    print(f"Split routes for manual review:  {summary['network_analysis']['split_review_route_count']:,}")
    print(f"Frequency scenario routes:       {summary['network_analysis']['frequency_sensitivity_trip_additions']:,}")
    print("\nFull summary:")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
