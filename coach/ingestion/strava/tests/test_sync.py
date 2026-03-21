from typing import Any
from unittest.mock import MagicMock

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.sync import sync_strava_for_user
from coach.persistence.repositories.activities import SupabaseActivityRepository

_RAW_ACTIVITY: dict[str, Any] = {
    'id': 1,
    'start_date': '2024-01-15T08:00:00Z',
    'elapsed_time': 3600,
    'sport_type': 'Run',
    'type': 'Run',
}


class TestSyncStravaForUser:
    def setup_method(self) -> None:
        self._strava_client = MagicMock(spec=StravaClient)
        self._activity_repo = MagicMock(spec=SupabaseActivityRepository)
        self._activity_repo.sync_cursor.return_value = 0
        self._strava_client.list_activities.return_value = iter([])

    def test_syncs_from_epoch_when_no_existing_activities(self) -> None:
        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.list_activities.assert_called_once_with(detailed=True, after=0)

    def test_syncs_from_last_activity_timestamp(self) -> None:
        self._activity_repo.sync_cursor.return_value = 1700000000

        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.list_activities.assert_called_once_with(detailed=True, after=1700000000)

    def test_returns_count_of_saved_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_RAW_ACTIVITY, _RAW_ACTIVITY])

        result = sync_strava_for_user(self._strava_client, self._activity_repo)

        assert result == 2

    def test_saves_mapped_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_RAW_ACTIVITY])

        sync_strava_for_user(self._strava_client, self._activity_repo)

        saved = self._activity_repo.save_many.call_args[0][0]
        assert len(saved) == 1
        assert saved[0].id == 1

    def test_returns_zero_when_no_new_activities(self) -> None:
        result = sync_strava_for_user(self._strava_client, self._activity_repo)

        assert result == 0

    def test_resets_table_before_syncing_when_fresh(self) -> None:
        sync_strava_for_user(self._strava_client, self._activity_repo, fresh=True)

        self._activity_repo.reset_table.assert_called_once()
