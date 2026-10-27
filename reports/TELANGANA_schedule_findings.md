# Telangana GTFS Schedule Quality Investigation



## Objective



Investigate trips flagged by the schedule audit for unusually long durations or large gaps between consecutive stops.



## Case 1: Route AL — Trip 41777461



- **Route:** AL

- **Direction ID:** 0

- **Service ID:** MTWTFSS

- **Trip short name:** AL-(RGIA-JBS)

- **Stops:** 10

- **Start time:** 01:25:00

- **End time:** 68:22:31

- **Duration:** Approximately 66.96 hours

- **Maximum gap between stops:** Approximately 11.50 hours

- **Audit status:** Time sequence passes basic checks

- **Duration flag:** Over 24 hours

- **Gap flag:** Gap over 2 hours

- **Extreme-gap flag:** Extreme gap over 4 hours



## Comparison Trip: 41777463



Trip 41777463 has the same route, direction, service ID, trip short name, and sequence of 10 stops.



- **Start time:** 18:55:00

- **End time:** 30:04:35

- **Duration:** Approximately 11.16 hours

- **Maximum gap between stops:** Approximately 1.91 hours



## Findings



Trip 41777461 is a strong candidate for manual schedule review because its duration and stop-to-stop gaps are substantially larger than those of the comparison trip.



The calendar defines service MTWTFSS for all seven days of the week, from 2026-02-01 through 2031-02-01. The Telangana feed does not contain `calendar_dates.txt` or `shapes.txt`.



GTFS permits times greater than 24:00:00 to represent times after midnight. Therefore, a time exceeding 24 hours is not, by itself, proof of invalid data.



## Recommended Action



- Preserve the original GTFS data.

- Flag trip 41777461 for manual review.

- Do not automatically delete or correct the trip.

- Investigate the source timetable before deciding whether the schedule is erroneous.



## Limitations



This investigation identifies a potential data-quality anomaly; it does not establish the intended timetable or prove the cause of the unusually long gaps.

