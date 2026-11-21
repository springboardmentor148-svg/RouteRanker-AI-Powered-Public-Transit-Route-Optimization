import argparse
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

GTFS_FILES = ["routes.txt", "trips.txt", "stop_times.txt", "stops.txt", "calendar.txt"]


def read_gtfs_zip(zip_file) -> dict:
    """Return the required GTFS members from an uploaded ZIP as in-memory files."""
    try:
        with ZipFile(zip_file) as archive:
            members_by_name = {}
            for member in archive.namelist():
                basename = Path(member).name
                if basename in GTFS_FILES and not member.endswith("/"):
                    members_by_name.setdefault(basename, []).append(member)

            missing = [name for name in GTFS_FILES if name not in members_by_name]
            if missing:
                raise ValueError("ZIP is missing required GTFS files: " + ", ".join(missing))

            duplicates = [name for name, members in members_by_name.items() if len(members) > 1]
            if duplicates:
                raise ValueError("ZIP contains multiple copies of: " + ", ".join(duplicates))

            return {
                filename: BytesIO(archive.read(members_by_name[filename][0]))
                for filename in GTFS_FILES
            }
    except BadZipFile as error:
        raise ValueError("The uploaded file is not a valid ZIP archive.") from error


def clean_gtfs_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates()

    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].astype("string").str.strip()

    df = df.replace(["", "NA", "N/A", "NULL", "null", "None"], pd.NA)

    if "route_type" in df:
        df["route_type"] = pd.to_numeric(df["route_type"], errors="coerce").astype("Int64")
    for column in ("stop_lat", "stop_lon", "stop_sequence", "timepoint", "direction_id"):
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def process_uploaded_gtfs(files: dict, city_name: str) -> dict:
    """Load uploaded/routes.txt-style file objects or paths and return cleaned DataFrames."""
    city_name = city_name.strip() or "uploaded-city"
    integrated = {}

    for filename in GTFS_FILES:
        source = files.get(filename)
        if source is None:
            continue

        df = pd.read_csv(source, low_memory=False)
        df = clean_gtfs_dataframe(df)
        df.insert(0, "city", city_name)

        output_name = filename.replace(".txt", "")
        integrated[output_name] = df

    result = dict(integrated)

    if "trips" in integrated:
        trips = integrated["trips"]
        if "route_id" in trips and "trip_id" in trips:
            result["route_trip_frequency"] = (
                trips.groupby(["city", "route_id"])["trip_id"]
                .nunique()
                .reset_index(name="trip_frequency")
            )

    if "stop_times" in integrated and "trips" in integrated:
        stop_times = integrated["stop_times"]
        trips = integrated["trips"]
        if "departure_time" in stop_times:
            stop_times = stop_times.copy()
            stop_times["hour_of_day"] = pd.to_numeric(
                stop_times["departure_time"].astype("string").str.split(":").str[0],
                errors="coerce",
            )
            result["stop_times"] = stop_times

        if {"city", "trip_id", "route_id"}.issubset(trips.columns) and "hour_of_day" in stop_times:
            hourly = stop_times.merge(
                trips[["city", "trip_id", "route_id"]].drop_duplicates(),
                on=["city", "trip_id"],
                how="inner",
            )
            result["hourly_route_frequency"] = (
                hourly.dropna(subset=["hour_of_day"])
                .groupby(["city", "route_id", "hour_of_day"])["trip_id"]
                .nunique()
                .reset_index(name="scheduled_trips")
            )

    return result


def integrate_gtfs(data_dir: Path, output_dir: Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = []
    output_frames = {name: [] for name in ("routes", "trips", "stop_times", "stops", "calendar")}

    for city_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        city = city_dir.name
        uploaded = {
            filename: city_dir / filename
            for filename in GTFS_FILES
            if (city_dir / filename).exists()
        }

        if not uploaded:
            continue

        processed = process_uploaded_gtfs(uploaded, city)
        for data_name, df in processed.items():
            if data_name in output_frames:
                output_frames[data_name].append(df)

        for filename in GTFS_FILES:
            source = uploaded.get(filename)
            status = "LOADED" if source is not None else "MISSING"
            record_count = len(processed[filename.replace(".txt", "")]) if status == "LOADED" else None
            inventory.append({"city": city, "file": filename, "status": status, "records": record_count})

    for name, frames in output_frames.items():
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(output_dir / f"{name}.csv", index=False)

    inventory_df = pd.DataFrame(inventory)
    inventory_df.to_csv(output_dir / "dataset_inventory.csv", index=False)

    route_frequency = []
    hourly_frequency = []
    for city_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        city = city_dir.name
        uploaded = {filename: city_dir / filename for filename in GTFS_FILES if (city_dir / filename).exists()}
        if uploaded:
            processed = process_uploaded_gtfs(uploaded, city)
            if "route_trip_frequency" in processed:
                route_frequency.append(processed["route_trip_frequency"])
            if "hourly_route_frequency" in processed:
                hourly_frequency.append(processed["hourly_route_frequency"])

    if route_frequency:
        pd.concat(route_frequency, ignore_index=True).to_csv(output_dir / "route_trip_frequency.csv", index=False)
    if hourly_frequency:
        pd.concat(hourly_frequency, ignore_index=True).to_csv(output_dir / "hourly_route_frequency.csv", index=False)

    return inventory_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Integrate GTFS .txt files by city.")
    parser.add_argument("--data-dir", type=Path, default=Path(r"E:\dataset"), help="Folder containing city subfolders")
    parser.add_argument("--output-dir", type=Path, default=Path(r"E:\Routeranker_proj"), help="Integrated CSV output folder")
    args = parser.parse_args()

    inventory = integrate_gtfs(args.data_dir, args.output_dir)
    print("Integration finished")
    print("Output folder:", args.output_dir)
    print(inventory.to_string(index=False))


if __name__ == "__main__":
    main()
