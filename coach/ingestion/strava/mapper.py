from typing import Any

from coach.domain.models import Activity
from coach.domain.models import ActivitySource
from coach.domain.models import SportType
from coach.utils import parse_utc_datetime


class StravaMapper:
    def map_strava_activity(self, payload: dict[str, Any]) -> Activity:
        start_time = parse_utc_datetime(payload['start_date'])

        return Activity(
            activity_id=int(payload['id']),
            source=ActivitySource.STRAVA,
            source_activity_id=int(payload['id']),
            sport_type=self._map_sport_type(payload),
            title=payload.get('title'),
            start_time_utc=start_time,
            elapsed_time_seconds=int(payload['elapsed_time']),
            moving_time_seconds=payload.get('moving_time'),
            distance_meters=payload.get('distance'),
            elevation_gain_meters=payload.get('total_elevation_gain'),
            average_heart_rate=payload.get('average_heartrate'),
            max_heart_rate=payload.get('max_heartrate'),
            average_power_watts=payload.get('average_watts'),
            is_manual=bool(payload.get('manual', False)),
            is_race=bool(payload.get('workout_type') == 1),
        )

    @staticmethod
    def _map_sport_type(payload: dict[str, str]) -> SportType:
        raw = payload.get('sport_type') or payload.get('type') or SportType.OTHER
        return SportType(raw) if raw in SportType._value2member_map_ else SportType.OTHER
