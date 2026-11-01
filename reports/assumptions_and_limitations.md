# RouteRanker – Module 2
## Assumptions and Limitations

### 1. Missing shapes.txt

The shapes.txt file was unavailable in all five city datasets:
- Hyderabad
- Bangalore
- Delhi
- Mumbai
- Pune

Therefore, geographical route length could not be calculated using GTFS shape data. Route length is excluded from the current feature-engineered dataset.

### 2. Scheduled Trips

Trip counts are calculated using distinct trip IDs from trips.txt. These represent scheduled trips, not actual completed trips.

### 3. Passenger Information

The available GTFS schedule data does not provide actual passenger counts or vehicle occupancy. Therefore, passenger demand and overcrowding cannot be determined from scheduled trip counts alone.

### 4. Missing Data

Some optional GTFS files may not be available in every city dataset. Only features supported by the available data will be calculated.

### 5. Time Information

Time-based features are derived from scheduled arrival and departure times in stop_times.txt. GTFS times greater than 24:00:00 are handled according to the GTFS time format.

### 6. Route Distance

Actual route distance is not included because shapes.txt is unavailable. No artificial route-length values have been created.

### 7. Data Quality

Missing values, duplicate records, invalid times and inconsistent identifiers will be checked before generating the final feature-engineered dataset.
### Delhi GTFS Data Quality Finding

During the initial data quality inspection of Delhi's GTFS dataset, 8 duplicate trip IDs were identified in `trips.txt`.

- Total trip records: 78,515
- Distinct duplicate trip IDs: 8
- Rows involved: 16
- Exact duplicate extra rows: 8
- Unique records after removing exact duplicates: 78,507

The identified duplicate rows have identical values across all columns. The original GTFS dataset is preserved without modification. These duplicate records will be handled during the data preprocessing stage.