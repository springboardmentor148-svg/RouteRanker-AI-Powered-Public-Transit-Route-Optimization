"""Display the CSV outputs created for Module 2 feature engineering.

Place this file in the project folder with the CSV files, then run:

    python module2_feature_engineering.py

By default, the script shows the first 20 data rows from each Module 2 output
CSV. Use ``--all`` to print every row, or ``--all-files`` to include input and
other CSV files as well.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence


FEATURE_FILE_PREFIXES = (
    "route_features",
    "route_hour_features",
    "stop_usage",
)
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}
MAX_COLUMN_WIDTH = 32


def find_csv_files(folder: Path) -> list[Path]:
    """Return CSV files below *folder*, skipping common environment folders."""
    files: list[Path] = []
    for path in folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".csv":
            continue
        if any(part.casefold() in SKIP_DIRECTORY_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda path: str(path).casefold())


def is_feature_output(path: Path) -> bool:
    """Recognize the Module 2 output names, including names such as ``(1)``."""
    stem = path.stem.casefold().lstrip()
    return any(stem.startswith(prefix) for prefix in FEATURE_FILE_PREFIXES)


def shorten(value: str, width: int) -> str:
    value = value.replace("\r", " ").replace("\n", " ")
    if len(value) <= width:
        return value
    return value[: width - 3] + "..."


def print_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Print a small dependency-free table, clipping unusually wide columns."""
    column_count = max([len(header), *(len(row) for row in rows)], default=0)
    if column_count == 0:
        print("(This CSV has no columns.)")
        return

    normalized_header = list(header) + [""] * (column_count - len(header))
    normalized_rows = [list(row) + [""] * (column_count - len(row)) for row in rows]
    widths = [
        min(
            MAX_COLUMN_WIDTH,
            max(3, len(normalized_header[index]), *(len(row[index]) for row in normalized_rows)),
        )
        for index in range(column_count)
    ]

    def format_row(row: Sequence[str]) -> str:
        cells = [shorten(row[index], widths[index]).ljust(widths[index]) for index in range(column_count)]
        return " | ".join(cells)

    print(format_row(normalized_header))
    print("-+-".join("-" * width for width in widths))
    for row in normalized_rows:
        print(format_row(row))


def display_csv(path: Path, base_folder: Path, limit: int | None) -> None:
    """Print a CSV's header and rows, keeping only *limit* rows for display."""
    print(f"\n### {path.relative_to(base_folder)}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)
            if header is None:
                print("(This CSV is empty.)")
                return

            visible_rows: list[list[str]] = []
            total_rows = 0
            for row in reader:
                total_rows += 1
                if limit is None or len(visible_rows) < limit:
                    visible_rows.append(row)

        print_table(header, visible_rows)
        if limit is not None and total_rows > len(visible_rows):
            print(f"Showing {len(visible_rows)} of {total_rows} data rows. Run with --all to show all rows.")
        else:
            print(f"{total_rows} data row(s)")
    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not read this CSV: {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the data in Module 2 feature-engineering CSV files."
    )
    parser.add_argument(
        "--directory",
        type=Path,
        help="Folder to search (defaults to the folder containing this script).",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=20,
        help="Maximum data rows to show per file (default: 20).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show every data row in each selected file.",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Show every CSV found, including integrated route input files.",
    )
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be at least 1")
    return args


def main() -> int:
    args = parse_args()
    folder = (args.directory or Path(__file__).parent).expanduser().resolve()
    if not folder.is_dir():
        print(f"Folder not found: {folder}")
        return 1

    csv_files = find_csv_files(folder)
    if args.all_files:
        selected_files = csv_files
    else:
        selected_files = [path for path in csv_files if is_feature_output(path)]
        if not selected_files:
            # If feature outputs have not been created yet, still show any CSVs
            # in the selected project folder so the script remains useful.
            selected_files = csv_files
            if selected_files:
                print("No Module 2 output CSVs were found; showing the available CSV files instead.")

    if not selected_files:
        print(f"No CSV files found under: {folder}")
        print("Put the CSV files beside this script, or pass their folder with --directory.")
        return 0

    print(f"Module 2 CSV data — {len(selected_files)} file(s) found in {folder}")
    print("Showing all rows." if args.all else f"Showing up to {args.rows} data rows per file.")
    row_limit = None if args.all else args.rows
    for path in selected_files:
        display_csv(path, folder, row_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
