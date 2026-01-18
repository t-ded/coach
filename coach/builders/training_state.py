from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC
from datetime import date
from datetime import datetime
from typing import Optional

from coach.domain.models import Activity
from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import TrainingState


def get_activities_between_dates(
    activities: Iterable[Activity],
    *,
    window_start: date,
    window_end: date,
) -> list[Activity]:
    return [activity for activity in activities if window_start <= activity.start_time_utc.date() <= window_end]


def categorize_activities_by_sport_type(activities: Iterable[Activity]) -> dict[SportType, list[Activity]]:
    categorized_activities: dict[SportType, list[Activity]] = defaultdict(list)
    for activity in activities:
        categorized_activities[activity.sport_type].append(activity)
    return categorized_activities


def build_training_state(
    activities: Iterable[Activity],
    *,
    window_start: date,
    window_end: date,
    generated_at: Optional[datetime] = None,
) -> TrainingState:
    """
    Build an aggregated TrainingState over an explicit time window.

    The window is inclusive of both start and end dates.
    """
    activities_between_dates = get_activities_between_dates(activities, window_start=window_start, window_end=window_end)
    categorized_activities = categorize_activities_by_sport_type(activities_between_dates)
    categorized_volume = {sport_type: ActivityVolume.from_activities(activities) for sport_type, activities in categorized_activities.items()}

    return TrainingState(
        generated_at=generated_at or datetime.now(tz=UTC),
        window_start=window_start,
        window_end=window_end,
        volume_by_sport=categorized_volume,
        last_activity_date=max((activity.start_time_utc.date() for activity in activities_between_dates), default=None),
    )
