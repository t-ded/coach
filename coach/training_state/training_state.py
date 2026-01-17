from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from typing import Mapping
from typing import Optional

from coach.domain.models import SportType
from coach.domain.models import Activity


@dataclass(frozen=True, kw_only=True, slots=True)
class ActivityVolume:
    distance_meters: Optional[float]
    duration_seconds: int
    num_activities: int

    @classmethod
    def from_activities(cls, activities: Iterable[Activity]) -> ActivityVolume:
        distance_meters = 0.0
        duration_seconds = 0
        num_activities = 0

        for activity in activities:
            duration_seconds += activity.moving_time_seconds or activity.elapsed_time_seconds
            num_activities += 1
            distance_meters += activity.distance_meters or 0.0

        return cls(
            distance_meters=distance_meters if distance_meters > 0 else None,
            duration_seconds=duration_seconds,
            num_activities=num_activities,
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class TrainingState:
    generated_at: datetime
    window_start: date
    window_end: date

    volume_by_sport: Mapping[SportType, ActivityVolume]
    last_activity_date: Optional[date]
