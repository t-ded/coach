from collections.abc import Iterable
from typing import Any
from typing import Optional

from coach.domain.activity import Activity
from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.utils import parse_utc_datetime


def map_activities(payloads: Iterable[dict[str, Any]]) -> list[Activity]:
    return [map_strava_activity(payload) for payload in payloads]


def map_strava_activity(payload: dict[str, Any]) -> Activity:
    return Activity(
        id=int(payload['id']),
        sport_type=_map_sport_type(payload),
        name=payload.get('name'),
        description=payload.get('description'),
        notes=payload.get('private_note'),
        start_time_utc=parse_utc_datetime(payload['start_date']),
        elapsed_time_seconds=int(payload['elapsed_time']),
        moving_time_seconds=payload.get('moving_time'),
        distance_meters=payload.get('distance'),
        elevation_gain_meters=payload.get('total_elevation_gain'),
        average_heart_rate=payload.get('average_heartrate'),
        max_heart_rate=payload.get('max_heartrate'),
        is_manual=bool(payload.get('manual', False)),
        is_race=bool(payload.get('workout_type') == 1),
        pbs=map_pbs(payload.get('best_efforts')),
    )


def _map_sport_type(payload: dict[str, str]) -> SportType:
    raw = payload.get('sport_type') or payload.get('type') or SportType.OTHER
    return SportType(raw) if raw in SportType._value2member_map_ else SportType.OTHER


def map_pbs(best_efforts: Optional[list[dict[str, Any]]]) -> list[BestEffort]:
    if not best_efforts:
        return []
    return [
        BestEffort(name=effort['name'], moving_time_seconds=effort['moving_time'])
        for effort in best_efforts
        if effort['pr_rank'] == 1
    ]
