\# RouteRanker — Module 1 Data Quality Visuals



This folder contains visualisations generated during Module 1 of RouteRanker, an AI-powered public transit route analysis and optimisation project.



\## Visualisations



\### 01 — City Dataset Overview

\*\*File:\*\* `01\_city\_dataset\_overview.png`



Compares the number of routes and scheduled trips across the eight analysed city datasets. This helps identify differences in dataset size before further analysis.



\### 02 — Route Distance Data Coverage

\*\*File:\*\* `02\_distance\_coverage.png`



Shows the percentage of routes with distance data in each city. Missing or partial distance coverage may limit distance-based analysis and route comparisons.



\### 03 — Schedule Duration Audit

\*\*File:\*\* `03\_schedule\_duration.png`



Summarises Telangana trip-duration audit categories. Trips flagged for unusually long durations require investigation; a flag alone does not establish that a schedule is incorrect.



\### 04 — Stop-Gap Analysis

\*\*File:\*\* `04\_stop\_gap\_analysis.png`



Shows the number of Telangana trips within the configured stop-gap threshold, trips with gaps over two hours, and trips with extreme gaps over four hours. Extreme-gap flags are a subset of the broader gap audit.



\### 05 — Schedule Anomaly Comparison

\*\*File:\*\* `05\_anomaly\_comparison.png`



Compares Telangana trips `41777461` and `41777463`. Both share the same route, direction, service ID, trip short name, and sequence of ten stops. The flagged trip has a substantially longer recorded duration and maximum stop-to-stop gap.



This comparison supports manual review; it does not prove that the flagged schedule is invalid.



\### 06 — Module 1 Quality Summary

\*\*File:\*\* `06\_module1\_quality\_summary.png`



Provides a consolidated summary of the analysed city datasets and Telangana schedule-audit findings.



\## Data Sources



The figures are generated from project reports, including:



\- `reports/city\_summary.csv`

\- `reports/TELANGANA\_schedule\_audit.csv`

\- `reports/TELANGANA\_schedule\_findings.md`



The Python script `create\_module1\_visuals.py` generates the figures from these reports.



\## Interpretation and Limitations



\- Audit thresholds are screening rules, not definitive proof of data errors.

\- GTFS permits times greater than `24:00:00` to represent service after midnight.

\- Missing route-distance data does not necessarily mean the route itself is invalid.

\- The source GTFS data should be preserved until any suspected issue is verified against the original timetable.

\- The figures describe data quality and coverage; they do not yet establish that a route should be merged, removed, or assigned a different service frequency.



\## Reproducing the Figures



From the project root, run:



```bash

python visuals/create\_module1\_visuals.py

```



The script expects the report files listed above to be available in the project.



