from unittest.mock import MagicMock
from unittest.mock import patch

from coach.ingestion.strava.deauthorize import deauthorize_athlete


class TestDeauthorizeAthlete:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()

        self._mock_token_repo = MagicMock()
        self._mock_activity_repo = MagicMock()
        self._mock_users_repo = MagicMock()

        mock_users_cls = MagicMock()
        mock_users_cls.find_user_id_by_strava_id.return_value = 'user-123'
        mock_users_cls.return_value = self._mock_users_repo

        self._patchers = [
            patch('coach.ingestion.strava.deauthorize.SupabaseStravaTokenRepository', return_value=self._mock_token_repo),
            patch('coach.ingestion.strava.deauthorize.SupabaseActivityRepository', return_value=self._mock_activity_repo),
            patch('coach.ingestion.strava.deauthorize.SupabaseUsersRepository', mock_users_cls),
        ]
        for p in self._patchers:
            p.start()

    def teardown_method(self) -> None:
        for p in self._patchers:
            p.stop()

    def test_deletes_tokens(self) -> None:
        deauthorize_athlete(42, self._secret_client)

        self._mock_token_repo.delete_tokens.assert_called_once_with('user-123')

    def test_deletes_all_activities(self) -> None:
        deauthorize_athlete(42, self._secret_client)

        self._mock_activity_repo.delete_all_for_user.assert_called_once()

    def test_clears_strava_user_id(self) -> None:
        deauthorize_athlete(42, self._secret_client)

        self._mock_users_repo.clear_strava_user_id.assert_called_once()

    def test_unknown_athlete_is_ignored(self) -> None:
        with patch('coach.ingestion.strava.deauthorize.SupabaseUsersRepository.find_user_id_by_strava_id', return_value=None):
            deauthorize_athlete(99, self._secret_client)

        self._mock_token_repo.delete_tokens.assert_not_called()
        self._mock_activity_repo.delete_all_for_user.assert_not_called()
        self._mock_users_repo.clear_strava_user_id.assert_not_called()
