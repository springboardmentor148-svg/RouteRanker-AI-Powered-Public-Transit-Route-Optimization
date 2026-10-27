
import os
import pandas as pd
import matplotlib.pyplot as plt

# RouteRanker Module 1: Data quality visuals
os.makedirs("visuals", exist_ok=True)

data = pd.read_csv("reports/city_summary.csv")

# Visual 1: City dataset overview
sorted_data = data.sort_values("total_routes", ascending=True)

fig, axes = plt.subplots(1, 2, figsize=(15, 7))

axes[0].barh(sorted_data["city"], sorted_data["total_routes"])
axes[0].set_title("Total Routes by City")
axes[0].set_xlabel("Number of routes")
axes[0].grid(axis="x", alpha=0.3)

for i, value in enumerate(sorted_data["total_routes"]):
    axes[0].text(value, i, " " + format(value, ","), va="center")

axes[1].barh(sorted_data["city"], sorted_data["total_scheduled_trips"])
axes[1].set_title("Scheduled Trips by City")
axes[1].set_xlabel("Number of scheduled trips")
axes[1].grid(axis="x", alpha=0.3)

for i, value in enumerate(sorted_data["total_scheduled_trips"]):
    axes[1].text(value, i, " " + format(value, ","), va="center")

fig.suptitle("RouteRanker - Module 1: City Dataset Overview", fontsize=15)
fig.tight_layout()
fig.savefig("visuals/01_city_dataset_overview.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/01_city_dataset_overview.png")

# Visual 2: Route distance-data coverage by city
coverage_data = data.sort_values("distance_coverage_percent", ascending=True)

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(
    coverage_data["city"],
    coverage_data["distance_coverage_percent"]
)

ax.set_title("RouteRanker - Route Distance Data Coverage by City")
ax.set_xlabel("Routes with distance data (%)")
ax.set_xlim(0, 110)
ax.grid(axis="x", alpha=0.3)

for bar, value in zip(bars, coverage_data["distance_coverage_percent"]):
    ax.text(
        max(bar.get_width(), 0) + 1,
        bar.get_y() + bar.get_height() / 2,
        "{:.2f}%".format(value),
        va="center"
    )

fig.tight_layout()
fig.savefig("visuals/02_distance_coverage.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/02_distance_coverage.png")
print("Distance coverage chart uses the city summary report.")
# Visual 3: Telangana schedule duration audit
audit = pd.read_csv("reports/TELANGANA_schedule_audit.csv")

duration_counts = audit["duration_flag"].value_counts()
duration_order = [
    "Within duration thresholds",
    "Over 4 hours",
    "Over 24 hours"
]
duration_counts = duration_counts.reindex(duration_order, fill_value=0)

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(duration_counts.index, duration_counts.values)

ax.set_title("RouteRanker - Telangana Schedule Duration Audit")
ax.set_xlabel("Number of trips")
ax.set_ylabel("Duration review category")
ax.grid(axis="x", alpha=0.3)

for bar, value in zip(bars, duration_counts.values):
    ax.text(
        value,
        bar.get_y() + bar.get_height() / 2,
        " " + format(int(value), ","),
        va="center"
    )

fig.tight_layout()
fig.savefig("visuals/03_schedule_duration.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/03_schedule_duration.png")
print("Note: Duration flags identify trips for review, not confirmed errors.")
# Visual 4: Telangana stop-gap audit
gap_counts = audit["gap_flag"].value_counts()
gap_order = [
    "Within gap threshold",
    "Gap over 2 hours"
]
gap_counts = gap_counts.reindex(gap_order, fill_value=0)

extreme_count = int(
    (audit["extreme_gap_flag"] == "Extreme gap over 4 hours").sum()
)

fig, axes = plt.subplots(1, 2, figsize=(13, 6))

bars = axes[0].barh(gap_counts.index, gap_counts.values)
axes[0].set_title("Scheduled Stop-Gap Review")
axes[0].set_xlabel("Number of trips")
axes[0].grid(axis="x", alpha=0.3)

for bar, value in zip(bars, gap_counts.values):
    axes[0].text(
        value,
        bar.get_y() + bar.get_height() / 2,
        " " + format(int(value), ","),
        va="center"
    )

axes[1].barh(["Extreme gaps over 4 hours"], [extreme_count])
axes[1].set_title("Extreme-Gap Flags")
axes[1].set_xlabel("Number of trips")
axes[1].grid(axis="x", alpha=0.3)
axes[1].text(
    extreme_count,
    0,
    " " + format(extreme_count, ","),
    va="center"
)

fig.suptitle("RouteRanker - Telangana Stop-Gap Audit", fontsize=14)
fig.tight_layout()
fig.savefig("visuals/04_stop_gap_analysis.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/04_stop_gap_analysis.png")
print("Note: Extreme-gap flags are included within the broader gap audit.")
# Visual 5: Telangana trip anomaly comparison
trip_ids = ["41777461", "41777463"]
durations = [66.96, 11.16]
max_gaps = [11.50, 1.91]

labels = [
    "Trip 41777461 (flagged)",
    "Trip 41777463 (comparison)"
]

fig, axes = plt.subplots(1, 2, figsize=(13, 6))

# Compare total trip duration
bars1 = axes[0].barh(labels, durations)
axes[0].set_title("Trip Duration Comparison")
axes[0].set_xlabel("Duration (hours)")
axes[0].grid(axis="x", alpha=0.3)

for bar, value in zip(bars1, durations):
    axes[0].text(
        value,
        bar.get_y() + bar.get_height() / 2,
        " {:.2f} h".format(value),
        va="center"
    )

# Compare maximum gaps between consecutive stops
bars2 = axes[1].barh(labels, max_gaps)
axes[1].set_title("Maximum Stop-to-Stop Gap")
axes[1].set_xlabel("Gap (hours)")
axes[1].grid(axis="x", alpha=0.3)

for bar, value in zip(bars2, max_gaps):
    axes[1].text(
        value,
        bar.get_y() + bar.get_height() / 2,
        " {:.2f} h".format(value),
        va="center"
    )

fig.suptitle(
    "RouteRanker - Telangana Schedule Anomaly Investigation",
    fontsize=14
)
fig.tight_layout()
fig.savefig("visuals/05_anomaly_comparison.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/05_anomaly_comparison.png")
print("Note: Comparison values are from TELANGANA_schedule_findings.md.")
print("The flagged trip requires manual review; this chart does not prove invalidity.")

# Visual 6: Module 1 data-quality summary

fig, ax = plt.subplots(figsize=(12, 7))
ax.axis("off")

summary_lines = [
    "ROUTERANKER — MODULE 1: DATA QUALITY SUMMARY",
    "",
    "DATASET OVERVIEW",
    "Cities analysed: 8",
    "Total routes: {:,}".format(int(data["total_routes"].sum())),
    "Scheduled trips: {:,}".format(int(data["total_scheduled_trips"].sum())),
    "",
    "TELANGANA SCHEDULE AUDIT",
    "Trips audited: {:,}".format(len(audit)),
    "Duration over 4 hours: {:,}".format(
        int((audit["duration_flag"] == "Over 4 hours").sum())
    ),
    "Duration over 24 hours: {:,}".format(
        int((audit["duration_flag"] == "Over 24 hours").sum())
    ),
    "Gaps over 2 hours: {:,}".format(
        int((audit["gap_flag"] == "Gap over 2 hours").sum())
    ),
    "Extreme gaps over 4 hours: {:,}".format(
        int((audit["extreme_gap_flag"] == "Extreme gap over 4 hours").sum())
    ),
    "",
    "INTERPRETATION",
    "Audit flags identify records for further investigation.",
    "Long schedules may be intentional in GTFS feeds.",
    "Preserve source data; verify anomalies before correction."
]

ax.text(
    0.05, 0.95,
    "\n".join(summary_lines),
    transform=ax.transAxes,
    va="top",
    ha="left",
    fontsize=12,
    family="monospace",
    linespacing=1.35
)

fig.tight_layout()
fig.savefig("visuals/06_module1_quality_summary.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Created: visuals/06_module1_quality_summary.png")