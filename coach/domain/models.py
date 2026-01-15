from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from enum import StrEnum


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
    title: Optional[str]

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
