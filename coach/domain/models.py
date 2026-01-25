from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from datetime import date
from datetime import datetime
from enum import Enum
from enum import StrEnum
from typing import Any
from typing import Optional
from typing import TypedDict

from coach.utils import parse_private_notes_activity_summary


class ActivitySource(Enum):
    STRAVA = 'Strava'


class SportType(StrEnum):
    RUN = 'Run'
    RIDE = 'Ride'
    SWIM = 'Swim'
    STRENGTH = 'WeightTraining'
    WALK = 'Walk'
    OTHER = 'Other'


@dataclass(frozen=True, kw_only=True, slots=True)
class Activity:
    """
    Canonical representation of a single training session.

    This model represents session-level facts only.
    Derived metrics (pace, load, zones, splits) are intentionally excluded.
    """

    # Identity
    activity_id: int
    source: ActivitySource
    source_activity_id: int

    # Classification
    sport_type: SportType
    name: Optional[str]
    description: Optional[str] = None
    notes: Optional[str] = None

    # Time
    start_time_utc: datetime
    elapsed_time_seconds: int
    moving_time_seconds: Optional[int] = None

    # Distance / effort
    distance_meters: Optional[float] = None
    elevation_gain_meters: Optional[float] = None

    # Intensity proxies
    average_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    average_power_watts: Optional[float] = None

    # Metadata
    is_manual: bool
    is_race: bool


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
class ActivitySummary:
    start_time_utc: datetime
    sport_type: SportType
    description: str

    duration_seconds: int
    distance_meters: Optional[float]
    elevation_gain_meters: Optional[float] = None
    average_heart_rate: Optional[float] = None

    @classmethod
    def from_activity(cls, activity: Activity) -> ActivitySummary:
        return cls(
            start_time_utc=activity.start_time_utc,
            sport_type=activity.sport_type,
            description=parse_private_notes_activity_summary(activity.notes),

            duration_seconds=activity.moving_time_seconds or activity.elapsed_time_seconds,
            distance_meters=activity.distance_meters,
            elevation_gain_meters=activity.elevation_gain_meters,
            average_heart_rate=activity.average_heart_rate,
        )


class WeeklyActivities(TypedDict):
    Monday: list[ActivitySummary]
    Tuesday: list[ActivitySummary]
    Wednesday: list[ActivitySummary]
    Thursday: list[ActivitySummary]
    Friday: list[ActivitySummary]
    Saturday: list[ActivitySummary]
    Sunday: list[ActivitySummary]


@dataclass(frozen=True, kw_only=True, slots=True)
class WeeklySummary:
    week_start: date
    week_end: date

    volume_by_sport: Mapping[SportType, ActivityVolume]
    activity_summaries: WeeklyActivities


@dataclass(frozen=True, kw_only=True, slots=True)
class RecentTrainingHistory:
    generated_at: datetime
    current_week_summary: WeeklySummary
    history_weekly_summaries: tuple[WeeklySummary, ...]  # Chronologically sorted - most recent is first


@dataclass(frozen=True, kw_only=True, slots=True)
class CoachResponse:
    summary: str
    observations: list[str] = field(metadata={'bullets': True})
    recommendations: list[str] = field(metadata={'bullets': True})
    confidence_notes: Optional[str] = field(default=None, metadata={'optional': True})

    @classmethod
    def headers(cls) -> list[str]:
        return [f'{f.name.replace('_', ' ').title()}' for f in fields(cls)]

    @classmethod
    def field_info(cls) -> dict[str, dict[str, Any]]:
        return {f.name: dict(f.metadata) for f in fields(cls)}
