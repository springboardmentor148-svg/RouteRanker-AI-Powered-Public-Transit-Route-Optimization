"""Exploratory analysis for the route feature CSVs produced by Module 2.

Run from the project folder with:

    python module3_eda.py

The script finds route_features, route_hour_features, and stop_usage CSVs
recursively, displays previews and data-quality summaries, and saves charts to
``reports/module3_eda``. Use ``--all-rows`` to display each full data table.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError as error:  # pragma: no cover - depends on the user's environment
    raise SystemExit(
        "Module 3 EDA needs pandas. Install it with: python -m pip install pandas matplotlib"
    ) from error

try:
    import matplotlib.pyplot as plt
except ImportError:  # Tables and data-quality summaries still work without charts.
    plt = None

try:
    from IPython.display import display as notebook_display
except ImportError:
    notebook_display = None


FILE_TYPES = {
    "route features": "route_features",
    "hourly route features": "route_hour_features",
    "stop usage": "stop_usage",
}
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}
PLOT_DIRECTORY = Path("reports") / "module3_eda"
MAX_HISTOGRAMS = 6
MAX_CORRELATION_COLUMNS = 12


def show_table(frame: pd.DataFrame, *, index: bool = True) -> None:
    """Display a DataFrame inline in a notebook or as readable console text."""
    if notebook_display is not None:
        notebook_display(frame)
    else:
        print(frame.to_string(index=index))


def discover_csv_files(folder: Path) -> list[Path]:
    """Find CSVs under a folder, ignoring common virtual environment folders."""
    paths = []
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.casefold() == ".csv":
            if not any(part.casefold() in SKIP_DIRECTORY_NAMES for part in path.parts):
                paths.append(path)
    return sorted(paths, key=lambda path: str(path).casefold())


def file_type(path: Path) -> str | None:
    """Identify Module 2 CSVs by their filename, including names containing (1)."""
    stem = path.stem.casefold().strip()
    for label, prefix in FILE_TYPES.items():
        if stem.startswith(prefix):
            return label
    return None


def city_from_filename(path: Path, kind: str | None) -> str:
    """Extract a readable city label from common Module 2 output filenames."""
    if kind is None:
        return "unknown"
    prefix = FILE_TYPES[kind]
    suffix = path.stem[len(prefix):]
    suffix = re.sub(r"^\s*\(\d+\)\s*", "", suffix).strip(" _-().")
    if not suffix or suffix.casefold() in {"engineered", "all", "combined"}:
        return "Bengaluru" if not suffix else "all routes"

    city = re.sub(r"[_-]+", " ", suffix).strip().casefold()
    aliases = {
        "banglore": "bengaluru",
        "bangalore": "bengaluru",
        "channie": "chennai",
        "chen nai": "chennai",
        "hydrabad": "hyderabad",
    }
    return aliases.get(city, city).title()


def selected_csv_files(folder: Path, all_files: bool) -> tuple[list[Path], bool]:
    all_csvs = discover_csv_files(folder)
    if all_files:
        return all_csvs, False
    module2_csvs = [path for path in all_csvs if file_type(path)]
    if module2_csvs:
        return module2_csvs, False
    return all_csvs, bool(all_csvs)


def data_quality_summary(frame: pd.DataFrame, path: Path, folder: Path, rows_to_show: int | None) -> dict[str, Any]:
    """Print one CSV's preview, schema, missing values, and simple summaries."""
    kind = file_type(path)
    city = city_from_filename(path, kind)
    if "city" in frame.columns:
        cities = frame["city"].dropna().astype(str).str.strip()
        cities = sorted({value for value in cities if value}, key=str.casefold)
        if len(cities) == 1:
            city = cities[0].title()
        elif len(cities) > 1:
            city = "Multiple cities"
    relative_name = path.relative_to(folder)

    print(f"\n{'=' * 88}")
    print(f"{relative_name}  |  {kind or 'CSV file'}  |  {city}")
    print(f"Rows: {len(frame):,}  |  Columns: {len(frame.columns):,}")
    print("\nData preview:")
    preview = frame if rows_to_show is None else frame.head(rows_to_show)
    show_table(preview)
    if rows_to_show is not None and len(frame) > len(preview):
        print(f"Showing {len(preview):,} of {len(frame):,} rows. Use --all-rows to display all rows.")

    print("\nColumn types and non-missing values:")
    info_rows = pd.DataFrame({
        "column": frame.columns,
        "type": [str(frame[column].dtype) for column in frame.columns],
        "non_missing": [int(frame[column].notna().sum()) for column in frame.columns],
        "missing": [int(frame[column].isna().sum()) for column in frame.columns],
    })
    show_table(info_rows, index=False)

    missing = frame.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    print("\nMissing values:")
    if missing.empty:
        print("No missing values found.")
    else:
        missing_frame = missing.rename("missing").to_frame()
        missing_frame["percent"] = (100 * missing_frame["missing"] / max(len(frame), 1)).round(1)
        show_table(missing_frame)

    print(f"\nExact duplicate rows: {int(frame.duplicated().sum()):,}")
    for identifier in ("route_id", "stop_id", "trip_id"):
        if identifier in frame.columns:
            print(f"Duplicate {identifier}: {int(frame[identifier].duplicated().sum()):,}")

    numeric = frame.select_dtypes(include="number")
    if not numeric.empty:
        print("\nNumeric feature summary:")
        show_table(numeric.describe().T.round(2))

    categorical_columns = [
        column for column in frame.columns
        if (
            pd.api.types.is_string_dtype(frame[column].dtype)
            or pd.api.types.is_bool_dtype(frame[column].dtype)
            or isinstance(frame[column].dtype, pd.CategoricalDtype)
        )
        and frame[column].nunique(dropna=True) <= 20
    ]
    if categorical_columns:
        print("\nSmall-category value counts (up to 10 values per column):")
        for column in categorical_columns:
            print(f"\n{column}:")
            counts = frame[column].value_counts(dropna=False).head(10).rename("rows").to_frame()
            show_table(counts)

    return {
        "file": str(relative_name),
        "type": kind or "other CSV",
        "city": city,
        "rows": len(frame),
        "columns": len(frame.columns),
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
    }


def save_charts(frame: pd.DataFrame, path: Path, output_folder: Path) -> list[Path]:
    """Save numeric histograms and a Spearman correlation chart when possible."""
    if plt is None:
        print("Charts skipped because matplotlib is not installed.")
        return []

    numeric = frame.select_dtypes(include="number").dropna(axis=1, how="all")
    if numeric.empty:
        print("Charts skipped because this file has no numeric columns.")
        return []

    output_dir = output_folder / PLOT_DIRECTORY
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem).strip("_") or "csv"
    written: list[Path] = []

    histogram_columns = [column for column in numeric.columns if numeric[column].nunique(dropna=True) > 1]
    histogram_columns = histogram_columns[:MAX_HISTOGRAMS]
    if histogram_columns:
        figure, axes = plt.subplots(len(histogram_columns), 1, figsize=(8, 3.1 * len(histogram_columns)))
        if len(histogram_columns) == 1:
            axes = [axes]
        for axis, column in zip(axes, histogram_columns):
            values = numeric[column].dropna()
            axis.hist(values, bins=min(25, max(5, int(values.nunique()))), color="#3977a8", edgecolor="white")
            axis.set_title(f"{column} distribution")
            axis.set_xlabel(column)
            axis.set_ylabel("Rows")
            median = values.median()
            axis.axvline(median, color="#d45d00", linestyle="--", label=f"Median: {median:.2f}")
            axis.legend()
        figure.suptitle(f"{path.stem}: numeric feature distributions", y=1.01)
        figure.tight_layout()
        chart_path = output_dir / f"{safe_stem}_distributions.png"
        figure.savefig(chart_path, dpi=150, bbox_inches="tight")
        written.append(chart_path)
        plt.show()
        plt.close(figure)

    correlation_columns = list(numeric.columns[:MAX_CORRELATION_COLUMNS])
    if len(correlation_columns) >= 2:
        correlation = numeric[correlation_columns].corr(method="spearman")
        size = max(7, min(14, 0.7 * len(correlation_columns) + 4))
        figure, axis = plt.subplots(figsize=(size, size * 0.82))
        image = axis.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
        axis.set_xticks(range(len(correlation_columns)), labels=correlation_columns, rotation=55, ha="right")
        axis.set_yticks(range(len(correlation_columns)), labels=correlation_columns)
        axis.set_title(f"{path.stem}: Spearman correlation")
        figure.colorbar(image, ax=axis, label="Correlation")
        if len(correlation_columns) <= 8:
            for row in range(len(correlation_columns)):
                for column in range(len(correlation_columns)):
                    value = correlation.iloc[row, column]
                    if pd.notna(value):
                        axis.text(column, row, f"{value:.2f}", ha="center", va="center", fontsize=8)
        figure.tight_layout()
        chart_path = output_dir / f"{safe_stem}_spearman_correlation.png"
        figure.savefig(chart_path, dpi=150, bbox_inches="tight")
        written.append(chart_path)
        plt.show()
        plt.close(figure)

    return written


def run_eda(
    directory: str | Path = ".",
    *,
    preview_rows: int | None = 10,
    all_files: bool = False,
    make_plots: bool = True,
    output_directory: str | Path | None = None,
) -> pd.DataFrame:
    """Run EDA on the Module 2 output CSVs and return a per-file summary."""
    folder = Path(directory).expanduser().resolve()
    output_folder = Path(output_directory).expanduser().resolve() if output_directory else Path(__file__).parent.resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Data folder was not found: {folder}")
    if preview_rows is not None and preview_rows < 1:
        raise ValueError("preview_rows must be at least 1 or None for every row")

    files, fallback = selected_csv_files(folder, all_files)
    if not files:
        print(f"No CSV files found under {folder}")
        print("Place the Module 2 CSVs in the project folder, or pass their location to run_eda().")
        return pd.DataFrame(columns=["file", "type", "city", "rows", "columns", "missing_cells", "duplicate_rows"])
    if fallback:
        print("No Module 2 output CSVs found; analysing the available CSV files instead.")

    print(f"Module 3 EDA: {len(files)} CSV file(s) found under {folder}")
    print("These files describe scheduled routes/stops. They do not contain passenger demand or occupancy.")
    if plt is None and make_plots:
        print("Install matplotlib to create charts: python -m pip install matplotlib")

    summaries = []
    for path in files:
        try:
            frame = pd.read_csv(path, encoding="utf-8-sig")
        except Exception as error:
            print(f"\nCould not read {path.relative_to(folder)}: {error}")
            continue

        summaries.append(data_quality_summary(frame, path, folder, preview_rows))
        if make_plots and plt is not None:
            chart_paths = save_charts(frame, path, output_folder)
            for chart_path in chart_paths:
                try:
                    shown_path = chart_path.relative_to(folder)
                except ValueError:
                    shown_path = chart_path
                print(f"Chart saved: {shown_path}")

    summary = pd.DataFrame(summaries)
    if not summary.empty:
        print("\n" + "=" * 88)
        print("Across-file summary")
        show_table(summary, index=False)

        route_files = summary[summary["type"] == "route features"]
        if len(route_files) > 1:
            print("\nRoute feature files by city/source (row counts and data quality):")
            show_table(route_files[["city", "rows", "columns", "missing_cells", "duplicate_rows", "file"]], index=False)

    print("\nInterpretation note: trip and stop counts are scheduled-service measures, not passenger counts.")
    print("Treat unusual routes as candidates for follow-up; these files alone cannot establish crowding or underuse.")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore Module 2 route-feature CSV files.")
    parser.add_argument(
        "--directory",
        type=Path,
        default=None,
        help="Project/data folder to search (default: project folder, then Downloads if needed).",
    )
    parser.add_argument("--rows", type=int, default=10, help="Rows to preview per CSV (default: 10).")
    parser.add_argument("--all-rows", action="store_true", help="Display every row in each selected CSV.")
    parser.add_argument("--all-files", action="store_true", help="Analyse every CSV, including integrated input files.")
    parser.add_argument("--no-plots", action="store_true", help="Skip chart creation.")
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be at least 1")
    return args


def main() -> int:
    args = parse_args()
    project_folder = Path(__file__).parent.resolve()
    data_folder = args.directory.expanduser().resolve() if args.directory else project_folder
    if args.directory is None and not any(file_type(path) for path in discover_csv_files(data_folder)):
        downloads_folder = Path.home() / "Downloads"
        if downloads_folder.is_dir() and any(file_type(path) for path in discover_csv_files(downloads_folder)):
            data_folder = downloads_folder

    run_eda(
        data_folder,
        preview_rows=None if args.all_rows else args.rows,
        all_files=args.all_files,
        make_plots=not args.no_plots,
        output_directory=project_folder,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
