
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# Search the processed Chennai file first
file_path = (
    BASE_DIR / "data" / "processed" / "chennai" / "stop_times.csv"
)

if not file_path.exists():
    print("Processed Chennai stop_times.csv was not found.")
else:
    found = False

    for chunk in pd.read_csv(
        file_path,
        dtype=str,
        chunksize=100_000,
        low_memory=False
    ):
        matching = chunk[
            chunk["trip_id"] == "SRR-40089_T1"
        ]

        if not matching.empty:
            print("\nMatching trip rows:")
            print(matching.to_string(index=False))
            found = True

    if not found:
        print("Trip SRR-40089_T1 was not found in the processed file.")
