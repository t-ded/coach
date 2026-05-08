from typing import cast

from coach.domain.activity import SportType
from coach.domain.training_analytics import TrainingTrends
from coach.domain.training_analytics import WeeklyTrendEntry
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklySummary


def _build_weekly_trend_entry(week: WeeklySummary) -> tuple[WeeklyTrendEntry, list[float]]:
    """Return (WeeklyTrendEntry, list of individual run distances in km) for a week."""
    running_km = 0.0
    total_duration_seconds = 0
    session_count = 0
    run_distances: list[float] = []

    for sport_type, volume in week.volume_by_sport.items():
        total_duration_seconds += volume.duration_seconds
        session_count += volume.num_activities
        if sport_type == SportType.RUN and volume.distance_meters:
            running_km += volume.distance_meters / 1000

    day_lists = cast(list[list[ActivitySummary]], list(week.activity_summaries.values()))
    for day_activities in day_lists:
        for activity in day_activities:
            if activity.sport_type == SportType.RUN and activity.distance_meters:
                run_distances.append(activity.distance_meters / 1000)

    entry = WeeklyTrendEntry(
        week_start=week.week_start,
        running_km=round(running_km, 1),
        total_duration_hours=round(total_duration_seconds / 3600, 1),
        session_count=session_count,
    )
    return entry, run_distances


def _compute_volume_trend(entries: list[WeeklyTrendEntry]) -> str:
    if len(entries) <= 1:
        return 'stable'

    recent_km = entries[-1].running_km
    prev_entries = entries[:-1]
    prev_km_values = [e.running_km for e in prev_entries]
    prev_avg = sum(prev_km_values) / len(prev_km_values)

    if prev_avg == 0:
        return 'stable'
    if recent_km > prev_avg * 1.10:
        return 'increasing'
    if recent_km < prev_avg * 0.90:
        return 'decreasing'
    return 'stable'


def build_training_trends(history: RecentTrainingHistory) -> TrainingTrends:
    # Take at most 4 completed weeks, most-recent first, then reverse for oldest-first display
    raw_weeks = list(history.history_weekly_summaries[:4])
    raw_weeks.reverse()  # oldest first

    entries: list[WeeklyTrendEntry] = []
    all_run_distances: list[float] = []

    for week in raw_weeks:
        entry, run_distances = _build_weekly_trend_entry(week)
        entries.append(entry)
        all_run_distances.extend(run_distances)

    running_entries = [e.running_km for e in entries if e.running_km > 0]
    four_week_avg_running_km = round(sum(running_entries) / len(running_entries), 1) if running_entries else None

    return TrainingTrends(
        weekly_entries=tuple(entries),
        four_week_avg_running_km=four_week_avg_running_km,
        volume_trend=_compute_volume_trend(entries),
        weeks_active=sum(1 for e in entries if e.session_count > 0),
        longest_run_km=round(max(all_run_distances), 1) if all_run_distances else None,
    )
