from unittest.mock import MagicMock
from unittest.mock import patch

from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.web.coaching import get_display_name
from coach.web.coaching import load_coaching_data


class TestGetDisplayName:
    def setup_method(self) -> None:
        self._users_repo = MagicMock(spec=SupabaseUsersRepository)

    def test_returns_first_word_of_display_name(self) -> None:
        self._users_repo.get_display_name.return_value = 'John Doe'
        assert get_display_name(self._users_repo, 'john@example.com') == 'John'

    def test_single_word_display_name_returned_as_is(self) -> None:
        self._users_repo.get_display_name.return_value = 'Alice'
        assert get_display_name(self._users_repo, 'alice@example.com') == 'Alice'

    def test_falls_back_to_email_prefix_when_no_display_name(self) -> None:
        self._users_repo.get_display_name.return_value = None
        assert get_display_name(self._users_repo, 'alice@example.com') == 'alice'


class TestLoadCoachingData:
    def setup_method(self) -> None:
        self._mock_activity_repo = MagicMock(spec=SupabaseActivityRepository)
        self._mock_activity_repo.sync_cursor.return_value = 0
        self._mock_activity_repo.list_all.return_value = []

        self._mock_profile_repo = MagicMock(spec=SupabaseUserProfileRepository)
        self._mock_profile_repo.load.return_value = None

        self._patchers = [
            patch('coach.web.coaching.create_secret_client'),
            patch('coach.web.coaching.StravaClient'),
            patch('coach.web.coaching.SupabaseActivityRepository', return_value=self._mock_activity_repo),
            patch('coach.web.coaching.SupabaseUserProfileRepository', return_value=self._mock_profile_repo),
            patch('coach.web.coaching.sync_strava_for_user'),
        ]
        started = [p.start() for p in self._patchers]
        self._mock_sync = started[-1]

        self._profile, self._activities = load_coaching_data('user-123', MagicMock())

    def teardown_method(self) -> None:
        for p in self._patchers:
            p.stop()

    def test_strava_sync_is_called(self) -> None:
        self._mock_sync.assert_called_once()

    def test_returns_profile_from_repo(self) -> None:
        assert self._profile is self._mock_profile_repo.load.return_value

    def test_returns_activities_from_repo(self) -> None:
        assert self._activities is self._mock_activity_repo.list_all.return_value
