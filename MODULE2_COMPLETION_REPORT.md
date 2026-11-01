ROUTERANKER – MODULE 2
FEATURE ENGINEERING COMPLETION REPORT
1. OBJECTIVE
To generate time-based and route-level features
from GTFS datasets for five Indian cities.
2. CITIES COVERED
1. Bangalore
2. Delhi
3. Hyderabad
4. Mumbai
5. Pune
3. FEATURE ENGINEERING
- Arrival hour and minute
- Departure hour and minute
- Time-period classification
- Hourly trip counts
- Route-wise hourly trip counts
- Route-level trip counts
- Distinct stop counts
- Average stops per trip
- Headway calculations
4. DATA QUALITY
- 20 GTFS files inspected.
- 40 GTFS validation checks passed.
- 8 exact duplicate rows identified in Delhi trips.txt.
- 341 routes without trip references identified.
- Missing values documented.
- Original GTFS files preserved.
5. OUTPUTS
All 13 compulsory Module 2 output files
are available in data/processed/module2/.
An additional route profile verification report
has also been generated.
6. CONCLUSION
Module 2 feature engineering outputs have been
generated for all five cities. The resulting
datasets provide scheduled service features for
further exploratory data analysis and preprocessing.
Note: GTFS scheduled data does not provide actual
passenger demand, occupancy, congestion or delays.
## 5. OUTPUTS
The Module 2 output folder contains the generated feature-engineering datasets and supporting reports for all five cities.
- Route profile and route-level features
- Hourly trip counts
- Route-wise hourly trip counts
- Time-period counts
- Headway features
- GTFS reading summary
- Feature dictionary
- Data quality and validation reports
- Routes without trips report
- Arrival and departure time features
**GitHub submission note:** The arrival and departure time feature CSVs are represented by 1,000-row sample files in this repository to avoid uploading very large files. The complete generated CSV files are retained locally in `data/processed/module2/`.
