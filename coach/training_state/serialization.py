from dataclasses import asdict
from datetime import date
from datetime import datetime
import json
from typing import Any

from coach.training_state.training_state import ActivityVolume
from coach.training_state.training_state import TrainingState


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
        'volume_by_sport': json.dumps({activity: serialize_activity_volume(volume) for activity, volume in state.volume_by_sport.items()}),
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
        volume_by_sport={sport: deserialize_activity_volume(volume) for sport, volume in volume_by_sport.items()},
        last_activity_date=date.fromisoformat(serialized["last_activity_date"]) if serialized["last_activity_date"] else None,
    )
