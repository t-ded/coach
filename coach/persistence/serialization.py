from dataclasses import asdict
from datetime import date
from datetime import datetime
from enum import Enum
from typing import Any

from coach.domain.activity import Activity
from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal


def _dates_to_isostrings(values: dict[str, Any]) -> dict[str, Any]:
    values_copy = values.copy()
    for key, value in values_copy.items():
        if isinstance(value, date):
            values_copy[key] = value.isoformat()
    return values_copy


def _enums_to_values(values: dict[str, Any]) -> dict[str, Any]:
    values_copy = values.copy()
    for key, value in values_copy.items():
        if isinstance(value, Enum):
            values_copy[key] = value.value
    return values_copy


def serialize_activity(activity: Activity) -> dict[str, Any]:
    serialized = asdict(activity)
    serialized = _dates_to_isostrings(serialized)
    serialized = _enums_to_values(serialized)
    return serialized


def serialize_goal(goal: TrainingGoal) -> dict[str, Any]:
    goal_date = goal.goal_date.isoformat() if isinstance(goal.goal_date, date) else goal.goal_date
    base: dict[str, Any] = {
        'name': goal.name,
        'sport': goal.sport_type.value,
        'goal_date': goal_date,
        'priority': goal.priority.value,
        'notes': goal.notes,
    }
    if isinstance(goal, DistanceActivityTrainingGoal):
        base['type'] = 'distance'
        base['goal_distance_meters'] = goal.goal_distance_meters
        base['goal_duration_seconds'] = goal.goal_duration_seconds
        base['goal_pace'] = goal.goal_pace
    else:
        base['type'] = 'base'
    return base


def deserialize_goal(raw: dict[str, Any]) -> TrainingGoal:
    kwargs: dict[str, Any] = {
        'name': raw['name'],
        'sport_type': SportType(raw['sport']),
        'goal_date': raw['goal_date'],
        'priority': Priority(raw['priority']),
        'notes': raw.get('notes'),
    }
    if raw.get('type') == 'distance':
        return DistanceActivityTrainingGoal(
            **kwargs,
            goal_distance_meters=raw['goal_distance_meters'],
            goal_duration_seconds=raw['goal_duration_seconds'],
            goal_pace=raw['goal_pace'],
        )
    return TrainingGoal(**kwargs)


def deserialize_activity(serialized: dict[str, Any]) -> Activity:
    pbs = [BestEffort(name=pb['name'], moving_time_seconds=pb['moving_time_seconds']) for pb in serialized['pbs']]

    return Activity(
        id=serialized['id'],
        sport_type=SportType(serialized['sport_type']),
        name=serialized['name'],
        description=serialized['description'],
        notes=serialized['notes'],
        start_time_utc=datetime.fromisoformat(serialized['start_time_utc']),
        elapsed_time_seconds=serialized['elapsed_time_seconds'],
        moving_time_seconds=serialized['moving_time_seconds'],
        distance_meters=serialized['distance_meters'],
        elevation_gain_meters=serialized['elevation_gain_meters'],
        average_heart_rate=serialized['average_heart_rate'],
        max_heart_rate=serialized['max_heart_rate'],
        is_manual=bool(serialized['is_manual']),
        is_race=bool(serialized['is_race']),
        pbs=pbs,
    )
