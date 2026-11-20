# MODULE 6: MODEL INFERENCE AND ROUTE OPTIMIZATION

## 1. Introduction
Module 6 applies trained machine learning models to public transportation data to analyze route patterns, identify unusual routes, and explore operational improvements.

## 2. Objectives
- Load trained models from Module 5.
- Perform K-Means, DBSCAN, Random Forest, and XGBoost inference.
- Identify unusual route patterns.
- Investigate GTFS data-quality issues.
- Simulate hypothetical schedule changes.
- Compare original and simulated results.

## 3. Model Inference

Four trained models were successfully loaded:
- K-Means
- DBSCAN
- Random Forest
- XGBoost

Classification dataset: 4,721 records.

K-Means analyzed 7,312 routes.

| Cluster | Routes |
|---|---:|
| 0 | 6525 |
| 1 | 180 |
| 2 | 227 |
| 3 | 380 |

DBSCAN results:

| Point Type | Count |
|---|---:|
| Core | 7305 |
| Border | 1 |
| Noise | 6 |

## 4. Route Investigation

Six routes were investigated.

Chennai:
- MTC-11347: 4 trips, 11 stops.
- MTC-13118: 2 trips, 13 stops.
- MTC-13124: 2 trips, 10 stops.

No missing stop references or identified time anomalies were found in the checks performed.

Hyderabad:
- Route 219: 2,087 trips; 1,680 exceeded 24 GTFS hours and 247 exceeded 48 hours.
- Route 300: 1,314 trips; two trips had extremely long calculated durations.
- Route 546: Four trips; average coordinate-based straight-line distance approximately 718.30 km. Two trips had stop gaps near 199 km.

These findings require verification with the GTFS data provider.

## 5. Hypothetical Schedule Optimization

A separate simulation dataset was created. A hypothetical 10% reduction was applied to six routes selected for investigation.

Due to whole-trip rounding, only Hyderabad routes 219 and 300 had reduced trip counts.

This is a mathematical simulation, not a validated operational recommendation.

## 6. Before-and-After Comparison

| Metric | Before | After |
|---|---:|---:|
| Route Count | 7312 | 7312 |
| Scheduled Trips | 216854 | 216514 |
| Stop Count (route-level sum) | 259447 | 259447 |
| Estimated Distance (km) | 157563.96 | 157563.96 |
| Operating Days (route-level sum) | 49874 | 49874 |

Scheduled trips decreased by 340, approximately 0.157%.

## 7. Visualizations

- Total scheduled trips before and after simulation.
- Route-level scheduled trips before and after simulation.

## 8. Deliverables

Nine CSV files and two PNG visualizations were saved.

## 9. Limitations

- Actual passenger-demand data was unavailable.
- DBSCAN noise does not automatically mean route inefficiency.
- GTFS times above 24 hours are not automatically invalid.
- Straight-line distance is not actual road distance.
- The schedule adjustment is hypothetical.
- Classification inference results are not independent test results.

## 10. Conclusion

Module 6 successfully applied trained machine learning models, analyzed unusual public transport route patterns, investigated GTFS data-quality issues, and created a hypothetical schedule simulation.

Further validation using passenger demand, verified route geometry, and operational requirements is necessary before implementing real-world changes.
