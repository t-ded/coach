from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from datetime import datetime
from datetime import timedelta

from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import WeeklyActivities


def get_week_start_week_end(center_date: date | datetime) -> tuple[date, date]:
    center_date = center_date.date() if isinstance(center_date, datetime) else center_date
    return (
        center_date - timedelta(days=center_date.weekday()),
        center_date + timedelta(days=(6 - center_date.weekday())),
    )


def get_activities_between_dates(
    activities: Iterable[Activity],
    *,
    window_start: date,
    window_end: date,
) -> list[Activity]:
    return [activity for activity in activities if window_start <= activity.start_time_utc.date() <= window_end]


def create_empty_weekly_activities() -> WeeklyActivities:
    return {
        'Monday': [],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [],
        'Saturday': [],
        'Sunday': [],
    }


def bucket_activities_by_weekday(activities: Iterable[Activity]) -> WeeklyActivities:
    buckets: WeeklyActivities = create_empty_weekly_activities()

    for activity in activities:
        activity_weekday = activity.start_time_utc.strftime('%A')
        buckets[activity_weekday].append(ActivitySummary.from_activity(activity))  # type: ignore[literal-required]

    return buckets


def categorize_activities_by_sport_type(activities: Iterable[Activity]) -> dict[SportType, list[Activity]]:
    categorized_activities: dict[SportType, list[Activity]] = defaultdict(list)
    for activity in activities:
        categorized_activities[activity.sport_type].append(activity)
    return categorized_activities


def get_categorized_volume(activities: Iterable[Activity]) -> dict[SportType, ActivityVolume]:
    categorized_activities = categorize_activities_by_sport_type(activities)
    return {sport_type: ActivityVolume.from_activities(activities) for sport_type, activities in categorized_activities.items()}
