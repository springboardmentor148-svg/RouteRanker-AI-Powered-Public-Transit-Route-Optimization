
from pathlib import Path
import pandas as pd

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

features = [
    {
        "feature_name": "city",
        "description": "Name of the city associated with the record.",
        "calculation": "Taken from the GTFS dataset folder.",
        "data_source": "GTFS dataset",
        "usage": "Compare route and schedule patterns across cities.",
        "limitation": "Different cities may use different data conventions."
    },
    {
        "feature_name": "route_id",
        "description": "Identifier assigned to a transit route.",
        "calculation": "Taken from routes.txt and linked using route_id.",
        "data_source": "routes.txt",
        "usage": "Identify and group scheduled trips by route.",
        "limitation": "Route IDs may not be unique across different cities."
    },
    {
        "feature_name": "distinct_trip_count",
        "description": "Number of unique scheduled trips assigned to a route.",
        "calculation": "Count distinct trip_id values grouped by route_id.",
        "data_source": "trips.txt",
        "usage": "Compare the scheduled service volume of routes.",
        "limitation": "Does not measure actual completed trips or passengers."
    },
    {
        "feature_name": "distinct_stop_count",
        "description": "Number of unique stops appearing in a route's scheduled trips.",
        "calculation": "Count distinct stop_id values linked to trips on each route.",
        "data_source": "trips.txt and stop_times.txt",
        "usage": "Understand the stop coverage represented by scheduled trips.",
        "limitation": "Does not establish the exact geographic route length."
    },
    {
        "feature_name": "service_hour",
        "description": "Scheduled hour of a trip's first stop departure.",
        "calculation": "Extract the hour from the first stop's departure_time; GTFS times can exceed 24:00.",
        "data_source": "stop_times.txt",
        "usage": "Group scheduled departures into service hours.",
        "limitation": "Represents scheduled time, not real-time operation."
    },
    {
        "feature_name": "scheduled_trip_count",
        "description": "Number of distinct scheduled trips for a route during a service hour.",
        "calculation": "Count distinct trip_id values grouped by city, route_id, and service_hour.",
        "data_source": "trips.txt and stop_times.txt",
        "usage": "Identify hours with relatively more or fewer scheduled trips.",
        "limitation": "Does not measure passenger demand or occupancy."
    },
    {
        "feature_name": "monday_to_sunday",
        "description": "Seven calendar flags indicating the days a service is scheduled.",
        "calculation": "Read the 0 or 1 values for each weekday in calendar.txt.",
        "data_source": "calendar.txt",
        "usage": "Summarize the scheduled operating days of each service.",
        "limitation": "Does not account for date-specific exceptions in calendar_dates.txt."
    },
    {
        "feature_name": "scheduled_operating_days_per_week",
        "description": "Number of weekdays marked as operating for a service.",
        "calculation": "Sum the Monday-to-Sunday flags in calendar.txt.",
        "data_source": "calendar.txt",
        "usage": "Compare weekly service patterns.",
        "limitation": "Does not confirm actual bus operation."
    },
    {
        "feature_name": "headway_minutes",
        "description": "Scheduled time gap in minutes between consecutive departures within a route/service group.",
        "calculation": "Difference between consecutive scheduled departure times.",
        "data_source": "Generated trip headway feature files",
        "usage": "Estimate scheduled service intervals and identify irregular gaps.",
        "limitation": "Missing values may occur for first departures; zero values can represent simultaneous departures."
    },
    {
        "feature_name": "Reference passenger count",
        "description": "Actual passenger count or occupancy.",
        "calculation": "Not calculated because passenger-count data is unavailable in the current project datasets.",
        "data_source": "Not available",
        "usage": "Would help assess real passenger demand if reliable data becomes available.",
        "limitation": "Must not be inferred from scheduled trip counts."
    },
]

dictionary = pd.DataFrame(features)

output_file = PROCESSED_DIR / "feature_dictionary.csv"
dictionary.to_csv(output_file, index=False)

print("Feature dictionary created successfully!")
print(f"Total documented features: {len(dictionary)}")
print(f"Saved to: {output_file}")

print("\nFeature names:")
for name in dictionary["feature_name"]:
    print(f"- {name}")
