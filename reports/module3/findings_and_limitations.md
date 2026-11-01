# Findings and limitations

- Peak hour(s): [15], with 58 starts each. Lowest nonzero hour(s): [21], with 4 starts each. Hours with no recorded starts: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22, 23]. Zeros describe this dataset; they do not establish source completeness.
- Highest-count route(s): ['1832']; lowest-count route(s): ['1890', '1881', '1882', '1889', '1887', '1843', '1844', '1888']. A lower scheduled trip count alone does not prove underutilisation.
- Route(s) ['1868'] have the largest recorded stop count: 13. Completeness of recorded stop lists requires separate verification.
- 2 route(s) have median shape estimates below 1 km. This is a review threshold, not an invalidity rule.
- Shared-stop overlap uses intersection/union of recorded stop IDs. It ignores direction, order and nearby stops with different IDs. It does not establish redundancy.
- Not produced: original Vapi GTFS files were not uploaded.

## Limitations

- Scope: Vapi feed and one service date only.
- Service date: 2026-10-31.
- Weekday/weekend comparison cannot be established from one date.
- Trip starts are counted once at each trip's first recorded stop.
- Hours above 23 remain separate service-day hours.
- Time periods use clock hours; their lengths differ.
- Missing or invalid numeric measurements are excluded from relevant summaries; original input files remain unchanged.
- Zero recorded starts do not establish that the source schedule is complete.
- Shape lengths estimate linked geometry and may be incomplete.
- Departure span describes first-to-last trip starts, not continuous service.
- Correlation uses available route pairs; sample sizes are saved.
- The small route sample and source issues can affect correlations.
- Outliers are retained; no automatic deletion or imputation is performed.
- Shared stops do not establish shared geographical segments or redundancy.
- Ridership, occupancy, costs, actual travel times and fleet information are needed for stronger operational conclusions.
- Scheduled trip counts cannot establish overcrowding or underutilisation.