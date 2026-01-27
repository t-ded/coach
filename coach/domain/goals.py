from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(kw_only=True, frozen=True, slots=True)
class TrainingGoal:
    sport_type: str
    name: str
    goal_date: str | date
    notes: Optional[str] = None


class DistanceActivityTrainingGoal(TrainingGoal):
    goal_distance_meters: float
    goal_duration_seconds: int
    goal_pace: str
