from datetime import UTC
from datetime import datetime

from coach.ingestion.strava.mapper import StravaMapper
from coach.domain.models import SportType


class TestStravaMapper:
    def setup_method(self) -> None:
        self._mapper = StravaMapper()

    def test_map_strava_activity_minimal(self) -> None:
        payload = {
            'id': 123,
            'sport_type': 'Run',
            'title': 'Morning Run',
            'start_date': '2024-01-01T07:00:00Z',
            'elapsed_time': 3_600,
            'moving_time': 3_500,
            'distance': 10_000.0,
            'total_elevation_gain': 120.0,
            'manual': False,
        }

        activity = self._mapper.map_strava_activity(payload)

        assert activity.source_activity_id == 123
        assert activity.sport_type == SportType.RUN
        assert activity.start_time_utc == datetime(2024, 1, 1, 7, 0, 0, tzinfo=UTC)
        assert activity.distance_meters == 10_000.0
        assert activity.is_race is False
