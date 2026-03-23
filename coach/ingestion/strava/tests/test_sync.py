from typing import Any
from unittest.mock import MagicMock
from unittest.mock import call

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.sync import sync_strava_for_user
from coach.persistence.repositories.activities import SupabaseActivityRepository

_SUMMARY_1: dict[str, Any] = {'id': 1}
_SUMMARY_2: dict[str, Any] = {'id': 2}

_DETAIL_1: dict[str, Any] = {
    'id': 1,
    'start_date': '2024-01-15T08:00:00Z',
    'elapsed_time': 3600,
    'sport_type': 'Run',
    'type': 'Run',
}
_DETAIL_2: dict[str, Any] = {
    'id': 2,
    'start_date': '2024-01-16T08:00:00Z',
    'elapsed_time': 1800,
    'sport_type': 'Run',
    'type': 'Run',
}


class TestSyncStravaForUser:
    def setup_method(self) -> None:
        self._strava_client = MagicMock(spec=StravaClient)
        self._activity_repo = MagicMock(spec=SupabaseActivityRepository)
        self._activity_repo.sync_cursor.return_value = 0
        self._activity_repo.existing_ids.return_value = set()
        self._strava_client.list_activities.return_value = iter([])

    def test_lists_summaries_from_cursor(self) -> None:
        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.list_activities.assert_called_once_with(detailed=False, after=0)

    def test_lists_from_last_activity_timestamp(self) -> None:
        self._activity_repo.sync_cursor.return_value = 1700000000

        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.list_activities.assert_called_once_with(detailed=False, after=1700000000)
        self._activity_repo.existing_ids.assert_called_once_with(1700000000)

    def test_fetches_details_only_for_new_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_SUMMARY_1, _SUMMARY_2])
        self._strava_client.get_detailed_activity.side_effect = [_DETAIL_1, _DETAIL_2]

        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.get_detailed_activity.assert_has_calls([call(1), call(2)])

    def test_skips_detail_fetch_for_existing_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_SUMMARY_1, _SUMMARY_2])
        self._activity_repo.existing_ids.return_value = {1}
        self._strava_client.get_detailed_activity.return_value = _DETAIL_2

        sync_strava_for_user(self._strava_client, self._activity_repo)

        self._strava_client.get_detailed_activity.assert_called_once_with(2)

    def test_returns_count_of_new_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_SUMMARY_1, _SUMMARY_2])
        self._strava_client.get_detailed_activity.side_effect = [_DETAIL_1, _DETAIL_2]

        result = sync_strava_for_user(self._strava_client, self._activity_repo)

        assert result == 2

    def test_returns_zero_when_no_new_activities(self) -> None:
        result = sync_strava_for_user(self._strava_client, self._activity_repo)

        assert result == 0

    def test_saves_mapped_activities(self) -> None:
        self._strava_client.list_activities.return_value = iter([_SUMMARY_1])
        self._strava_client.get_detailed_activity.return_value = _DETAIL_1

        sync_strava_for_user(self._strava_client, self._activity_repo)

        saved = self._activity_repo.save_many.call_args[0][0]
        assert len(saved) == 1
        assert saved[0].id == 1

    def test_resets_table_before_syncing_when_fresh(self) -> None:
        sync_strava_for_user(self._strava_client, self._activity_repo, fresh=True)

        self._activity_repo.reset_table.assert_called_once()
