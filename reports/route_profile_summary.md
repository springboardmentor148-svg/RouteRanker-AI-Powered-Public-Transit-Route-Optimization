# Route Profile Summary — RouteRanker Module 2

**Dataset:** `processed/route_features.csv`  
**Scope:** 9,915 bus and BRT routes across 8 Indian transit systems  

---

## 1. Per-City Route Profile Summary

The table below presents the verified median operational metrics for all 8 cities computed directly from the GTFS datasets:

| City / System | Total Routes | Median `trip_count` | Median `stop_count` | Median `route_length_km` | Median `headway_min` | Primary Length Method |
|---|---:|---:|---:|---:|---:|:---:|
| **Ahmedabad** | 978 | 8.0 | 40.0 | 17.79 km | 40.0 min | Stop Straight-Line |
| **Bengaluru** (BMTC) | 4,434 | 3.0 | 44.0 | 19.38 km | 100.0 min | Road Shape Polyline |
| **Davangere** | 93 | 46.0 | 31.5 | 11.19 km | 10.0 min | Stop Straight-Line |
| **Delhi** (DTC/DIMTS) | 1,270 | 33.0 | 39.0 | 20.39 km | 10.0 min | Stop Straight-Line |
| **HDBRT** (Hubli-Dharwad) | 632 | 5.0 | 19.0 | 7.75 km | 60.0 min | Stop Straight-Line |
| **Mumbai** (BEST) | 1,609 | 65.0 | 25.0 | 8.99 km | 15.0 min | Stop Straight-Line |
| **Pune** (PMPML) | 628 | 11.0 | 42.5 | 19.80 km | 45.0 min | Road Shape Polyline |
| **Rajkot** (RMTS/BRTS) | 271 | 8.0 | 30.0 | 14.20 km | 60.0 min | Stop Straight-Line |
| **ALL CITIES COMBINED** | **9,915** | **11.0** | **38.0** | **17.84 km** | **45.0 min** | — |

### Key Operational Observations:
1. **Network Specialization**:
   - **Mumbai (BEST)** operates the highest median trip volume per route (**65 trips/day**) with a tight **15-minute headway**, reflecting a dense, high-frequency feeder network (median length only 8.99 km).
   - **Bengaluru (BMTC)** has the largest route catalog (**4,434 routes**) with a longer median length (**19.38 km**), but a very low median frequency (**3 trips/day**, 100-minute headway), indicating extensive branch/feeder operations with specialized schedules.
   - **Delhi** features high frequency (**33 trips/day**) and short headways (**10.0 min**) across long radial routes (**20.39 km**).
2. **BRT vs. Conventional Transit**:
   - **HDBRT** operates compact corridors (median 7.75 km, 19 stops) serving rapid transit stations.

---

## 2. Real Example Route Profiles

Below are three representative route records extracted directly from `processed/route_features.csv`:

### Example 1: Bengaluru Arterial Route (Measured with Shape)
- **City**: `bengaluru`
- **Route ID**: `bengaluru_1083` (`original_route_id`: `1083`)
- **Route Short Name**: `G-6`
- **Route Long Name**: `Shirke KHB Quarters ⇔ Shanthinagara Bus Station`
- **Daily Trip Count**: 12 scheduled trips
- **Distinct Stops**: 58 physical stops
- **Route Length**: **19.88 km**
- **Length Method**: `shape` (verified from GPS road polyline vertices in `shapes.txt`)
- **Median Headway**: **100.0 minutes**
- **Time Window Breakdown**: Morning: 4 | Afternoon: 5 | Evening: 3 | Night: 0
- **Weekly Schedule**: Weekday trips: 12 | Weekend trips: 12
- **Operating Window**: 05:00 to 20:00 (Service Span: **15.42 hours**)
- **Active Days**: Monday through Sunday (All days)

### Example 2: Delhi Late-Evening Trunk Route (Stop Fallback)
- **City**: `delhi`
- **Route ID**: `delhi_986` (`original_route_id`: `986`)
- **Route Short Name**: *NaN* (Delhi GTFS omits `route_short_name` across all routes)
- **Route Long Name**: `156STLDOWN`
- **Daily Trip Count**: 11 scheduled trips
- **Distinct Stops**: 11 physical stops
- **Route Length**: **5.52 km**
- **Length Method**: `stop_straight_line_estimate`
- **Median Headway**: **10.0 minutes**
- **Time Window Breakdown**: Morning: 0 | Afternoon: 0 | Evening: 2 | Night: 9
- **Weekly Schedule**: Weekday trips: 11 | Weekend trips: 11
- **Operating Window**: 20:00 to 22:00 (Service Span: **1.67 hours**)
- **Active Days**: Monday through Sunday

### Example 3: Mumbai High-Frequency Feeder Route (Stop Fallback)
- **City**: `mumbai`
- **Route ID**: `mumbai_BEST_4424` (`original_route_id`: `BEST_4424`)
- **Route Short Name**: `207 AS`
- **Route Long Name**: `DAHISAR BUS STATION to MALVANI DEPOT; GAIKWAD NAGAR (DOWN)`
- **Daily Trip Count**: **65 scheduled trips**
- **Distinct Stops**: 48 physical stops
- **Route Length**: **13.60 km**
- **Length Method**: `stop_straight_line_estimate`
- **Median Headway**: **14.5 minutes**
- **Time Window Breakdown**: Morning: 25 | Afternoon: 14 | Evening: 15 | Night: 11
- **Weekly Schedule**: Weekday trips: 65 | Weekend trips: 65
- **Operating Window**: 06:00 to 23:00 (Service Span: **17.17 hours**)
- **Active Days**: Monday through Sunday
