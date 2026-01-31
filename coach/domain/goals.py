from dataclasses import dataclass
from datetime import date
from typing import Optional

from coach.domain.activity import SportType


@dataclass(kw_only=True, frozen=True, slots=True)
class TrainingGoal:
    sport_type: SportType
    name: str
    goal_date: str | date
    notes: Optional[str] = None


@dataclass(kw_only=True, frozen=True, slots=True)
class DistanceActivityTrainingGoal(TrainingGoal):
    goal_distance_meters: float
    goal_duration_seconds: int
    goal_pace: str
