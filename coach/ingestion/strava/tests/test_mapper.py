from datetime import UTC
from datetime import datetime
from typing import Any

from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.ingestion.strava.mapper import map_activities
from coach.ingestion.strava.mapper import map_pbs
from coach.ingestion.strava.mapper import map_strava_activity


def _base_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'id': 123,
        'sport_type': 'Run',
        'start_date': '2024-01-01T07:00:00Z',
        'elapsed_time': 3_600,
    }
    payload.update(overrides)
    return payload


class TestStravaMapperMapActivity:
    def test_maps_required_fields(self) -> None:
        activity = map_strava_activity(_base_payload())
        assert activity.id == 123
        assert activity.sport_type == SportType.RUN
        assert activity.start_time_utc == datetime(2024, 1, 1, 7, 0, 0, tzinfo=UTC)
        assert activity.elapsed_time_seconds == 3_600

    def test_optional_fields_are_none_when_absent(self) -> None:
        activity = map_strava_activity(_base_payload())
        assert activity.name is None
        assert activity.description is None
        assert activity.notes is None
        assert activity.moving_time_seconds is None
        assert activity.distance_meters is None
        assert activity.elevation_gain_meters is None
        assert activity.average_heart_rate is None
        assert activity.max_heart_rate is None

    def test_maps_optional_fields_when_present(self) -> None:
        payload = _base_payload(
            name='Morning Run',
            description='Easy pace',
            private_note='$felt good$',
            moving_time=3_500,
            distance=10_000.0,
            total_elevation_gain=120.0,
            average_heartrate=145.0,
            max_heartrate=165.0,
        )
        activity = map_strava_activity(payload)
        assert activity.name == 'Morning Run'
        assert activity.description == 'Easy pace'
        assert activity.notes == '$felt good$'
        assert activity.moving_time_seconds == 3_500
        assert activity.distance_meters == 10_000.0
        assert activity.elevation_gain_meters == 120.0
        assert activity.average_heart_rate == 145.0
        assert activity.max_heart_rate == 165.0

    def test_is_race_when_workout_type_is_1(self) -> None:
        activity = map_strava_activity(_base_payload(workout_type=1))
        assert activity.is_race is True

    def test_is_not_race_for_other_workout_types(self) -> None:
        assert map_strava_activity(_base_payload(workout_type=0)).is_race is False
        assert map_strava_activity(_base_payload(workout_type=2)).is_race is False
        assert map_strava_activity(_base_payload()).is_race is False

    def test_is_manual_true(self) -> None:
        activity = map_strava_activity(_base_payload(manual=True))
        assert activity.is_manual is True

    def test_is_manual_false_by_default(self) -> None:
        activity = map_strava_activity(_base_payload())
        assert activity.is_manual is False


class TestStravaMapperSportType:
    def test_maps_known_sport_type(self) -> None:
        assert map_strava_activity(_base_payload(sport_type='Run')).sport_type == SportType.RUN
        assert map_strava_activity(_base_payload(sport_type='Ride')).sport_type == SportType.RIDE

    def test_falls_back_to_type_field_when_sport_type_absent(self) -> None:
        payload = _base_payload()
        del payload['sport_type']
        payload['type'] = 'Run'
        assert map_strava_activity(payload).sport_type == SportType.RUN

    def test_falls_back_to_other_for_unknown_sport_type(self) -> None:
        assert map_strava_activity(_base_payload(sport_type='Kayaking')).sport_type == SportType.OTHER

    def test_falls_back_to_other_when_both_fields_absent(self) -> None:
        payload = _base_payload()
        del payload['sport_type']
        assert map_strava_activity(payload).sport_type == SportType.OTHER


class TestStravaMapperMapPbs:
    def test_returns_empty_list_when_no_best_efforts(self) -> None:
        assert map_pbs(None) == []
        assert map_pbs([]) == []

    def test_only_includes_rank_1_efforts(self) -> None:
        efforts = [
            {'name': '5K', 'moving_time': 1200, 'pr_rank': 1},
            {'name': '10K', 'moving_time': 2500, 'pr_rank': 2},
            {'name': '1K', 'moving_time': 240, 'pr_rank': None},
        ]
        assert map_pbs(efforts) == [BestEffort(name='5K', moving_time_seconds=1200)]

    def test_maps_multiple_rank_1_efforts(self) -> None:
        efforts = [
            {'name': '5K', 'moving_time': 1200, 'pr_rank': 1},
            {'name': '10K', 'moving_time': 2500, 'pr_rank': 1},
        ]
        assert len(map_pbs(efforts)) == 2

    def test_pbs_available_on_mapped_activity(self) -> None:
        payload = _base_payload(
            best_efforts=[
                {'name': '5K', 'moving_time': 1200, 'pr_rank': 1},
            ],
        )
        assert map_strava_activity(payload).pbs == [BestEffort(name='5K', moving_time_seconds=1200)]


class TestStravaMapperMapActivities:
    def test_maps_batch(self) -> None:
        activities = map_activities([_base_payload(id=i) for i in range(3)])
        assert len(activities) == 3
        assert [a.id for a in activities] == [0, 1, 2]

    def test_empty_batch(self) -> None:
        assert map_activities([]) == []
