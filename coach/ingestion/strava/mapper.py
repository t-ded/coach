from collections.abc import Iterable
from datetime import date
from typing import Any

from more_itertools import flatten

from coach.builders.utils import compute_distance_duration_pace
from coach.domain.activity import Activity
from coach.domain.activity import ActivitySource
from coach.domain.activity import SportType
from coach.domain.personal_bests import RUNNING_PBS_METERS_MAPPING
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.utils import parse_utc_datetime


class StravaMapper:
    def map_activities(self, payloads: Iterable[dict[str, Any]]) -> list[Activity]:
        return [self.map_strava_activity(payload) for payload in payloads]

    def map_strava_activity(self, payload: dict[str, Any]) -> Activity:
        start_time = parse_utc_datetime(payload['start_date'])

        return Activity(
            activity_id=int(payload['id']),
            source=ActivitySource.STRAVA,
            source_activity_id=int(payload['id']),
            sport_type=self._map_sport_type(payload),
            name=payload.get('name'),
            description=payload.get('description'),
            notes=payload.get('private_note'),
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

    def map_pbs(self, payloads: Iterable[dict[str, Any]]) -> RunningPersonalBestsSummary:
        all_best_efforts = flatten(best_effort for x in payloads if (best_effort := x.get('best_efforts')))
        pbs: dict[str, RunningPersonalBest] = {}

        for effort in all_best_efforts:
            if effort['pr_rank'] == 1 and effort['name'] in RUNNING_PBS_METERS_MAPPING:
                pbs[effort['name']] = self._get_running_pb(effort)

        return RunningPersonalBestsSummary.from_pbs(pbs)

    @staticmethod
    def _get_running_pb(effort: dict[str, Any]) -> RunningPersonalBest:
        moving_time_seconds: int = effort['moving_time']
        distance_meters = RUNNING_PBS_METERS_MAPPING[effort['name']]
        return RunningPersonalBest(
            DATE=date.fromisoformat(effort['start_date_local'][:10]),
            PACE_STR=compute_distance_duration_pace(distance_meters=distance_meters, duration_seconds=moving_time_seconds, pace_str=None)[2],
        )
