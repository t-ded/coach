import json
from dataclasses import asdict
from datetime import date
from datetime import datetime
from enum import Enum
from typing import Any

from coach.domain.models import Activity
from coach.domain.models import ActivitySource
from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import TrainingState


def _bools_to_ints(values: dict[str, Any]) -> dict[str, Any]:
    values_copy = values.copy()
    for key, value in values_copy.items():
        if isinstance(value, bool):
            values_copy[key] = int(value)
    return values_copy


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
    serialized = _bools_to_ints(serialized)
    serialized = _dates_to_isostrings(serialized)
    serialized = _enums_to_values(serialized)
    return serialized


def deserialize_activity(serialized: dict[str, Any]) -> Activity:
    return Activity(
        activity_id=serialized['activity_id'],
        source=ActivitySource(serialized['source']),
        source_activity_id=serialized['source_activity_id'],

        sport_type=SportType(serialized['sport_type']),
        name=serialized['name'],

        start_time_utc=datetime.fromisoformat(serialized['start_time_utc']),
        elapsed_time_seconds=serialized['elapsed_time_seconds'],
        moving_time_seconds=serialized['moving_time_seconds'],

        distance_meters=serialized['distance_meters'],
        elevation_gain_meters=serialized['elevation_gain_meters'],

        average_heart_rate=serialized['average_heart_rate'],
        max_heart_rate=serialized['max_heart_rate'],
        average_power_watts=serialized['average_power_watts'],

        is_manual=bool(serialized['is_manual']),
        is_race=bool(serialized['is_race']),
    )


def serialize_activity_volume(volume: ActivityVolume) -> dict[str, Any]:
    return asdict(volume)


def deserialize_activity_volume(serialized: dict[str, Any]) -> ActivityVolume:
    return ActivityVolume(
        distance_meters=serialized['distance_meters'],
        duration_seconds=serialized['duration_seconds'],
        num_activities=serialized['num_activities'],
    )


def serialize_training_state(state: TrainingState) -> dict[str, Any]:
    return {
        'generated_at': state.generated_at.isoformat(),
        'window_start': state.window_start.isoformat(),
        'window_end': state.window_end.isoformat(),
        'volume_by_sport': json.dumps({sport.value: serialize_activity_volume(volume) for sport, volume in state.volume_by_sport.items()}),
        'last_activity_date': (
            state.last_activity_date.isoformat()
            if state.last_activity_date
            else None
        ),
    }


def deserialize_training_state(serialized: dict[str, Any]) -> TrainingState:
    volume_by_sport = json.loads(serialized['volume_by_sport'])
    return TrainingState(
        generated_at=datetime.fromisoformat(serialized["generated_at"]),
        window_start=date.fromisoformat(serialized["window_start"]),
        window_end=date.fromisoformat(serialized["window_end"]),
        volume_by_sport={SportType(sport): deserialize_activity_volume(volume) for sport, volume in volume_by_sport.items()},
        last_activity_date=date.fromisoformat(serialized["last_activity_date"]) if serialized["last_activity_date"] else None,
    )
