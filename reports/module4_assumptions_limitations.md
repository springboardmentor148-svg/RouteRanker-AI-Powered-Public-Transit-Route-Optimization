# Module 4 - Assumptions, limitations and challenges

_Generated 2026-10-30._

## Assumptions

* A speed outside 3-80 km/h cannot come from a real timetable and is treated as invalid.
* Skew limit 1.0, near-constant limit 95% and correlation limit 0.95 are standard rules of thumb, not tuned on results.
* Median imputation assumes that a single-departure route is, for distance purposes, 'typical' in headway; the indicator column keeps the difference visible.

## Limitations

* **No ground truth and no passenger data:** nothing here shows which routes are overcrowded or underutilised; the next module can only group routes by similarity of scheduled service.
* The features are scheduled values; several feeds are community-made or old, and some show generated-looking timetables (Delhi, Kochi, Pune).
* Excluding Hyderabad is a judgement; its routes are not represented in the pooled clusters.
* Route length from stop coordinates is a straight-line lower bound for most feeds; `length_method` is kept so the model can see which routes have shape-based length.
* Grouping by route name keeps variants of a line together, but different lines that share stops can still be similar across the split.

## Challenges

* Deciding what to do with 16% missing headways without inventing a value (solved with median + indicator after showing the value is undefined).
* Choosing what to do with feeds that are not comparable (excluded, documented, reversible).
* Avoiding leakage between up/down variants of the same line (grouped split).
* Not creating a classification target because no valid label exists.
