from unittest.mock import MagicMock
from unittest.mock import patch

from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.web.chainlit_app import _get_display_name
from coach.web.chainlit_app import _is_done
from coach.web.chainlit_app import _load_coaching_data
from coach.web.chainlit_app import _strip_done


class TestIsDone:
    def test_returns_true_for_done_at_end(self) -> None:
        assert _is_done('Nice work. DONE') is True

    def test_returns_true_with_punctuation(self) -> None:
        assert _is_done('Great session! DONE.') is True

    def test_returns_true_case_insensitive(self) -> None:
        assert _is_done('done') is True

    def test_returns_false_when_done_not_at_end(self) -> None:
        assert _is_done('DONE but there is more') is False

    def test_returns_false_for_regular_message(self) -> None:
        assert _is_done('Keep up the good work!') is False


class TestStripDone:
    def test_strips_done_from_end(self) -> None:
        assert _strip_done('Nice work. DONE') == 'Nice work.'

    def test_strips_done_with_exclamation(self) -> None:
        assert _strip_done('Great session! DONE!') == 'Great session!'

    def test_no_change_when_no_done(self) -> None:
        assert _strip_done('Keep it up!') == 'Keep it up!'

    def test_strips_done_leaving_empty_string(self) -> None:
        assert _strip_done('DONE') == ''


class TestGetDisplayName:
    def setup_method(self) -> None:
        self._users_repo = MagicMock(spec=SupabaseUsersRepository)

    def test_returns_first_word_of_display_name(self) -> None:
        self._users_repo.get_display_name.return_value = 'John Doe'
        assert _get_display_name(self._users_repo, 'john@example.com') == 'John'

    def test_single_word_display_name_returned_as_is(self) -> None:
        self._users_repo.get_display_name.return_value = 'Alice'
        assert _get_display_name(self._users_repo, 'alice@example.com') == 'Alice'

    def test_falls_back_to_email_prefix_when_no_display_name(self) -> None:
        self._users_repo.get_display_name.return_value = None
        assert _get_display_name(self._users_repo, 'alice@example.com') == 'alice'


class TestLoadCoachingData:
    def setup_method(self) -> None:
        self._mock_activity_repo = MagicMock(spec=SupabaseActivityRepository)
        self._mock_activity_repo.sync_cursor.return_value = 0
        self._mock_activity_repo.list_all.return_value = []

        self._mock_profile_repo = MagicMock(spec=SupabaseUserProfileRepository)
        self._mock_profile_repo.load.return_value = None

        self._patchers = [
            patch('coach.web.chainlit_app.create_secret_client'),
            patch('coach.web.chainlit_app.StravaClient'),
            patch('coach.web.chainlit_app.SupabaseActivityRepository', return_value=self._mock_activity_repo),
            patch('coach.web.chainlit_app.SupabaseUserProfileRepository', return_value=self._mock_profile_repo),
            patch('coach.web.chainlit_app.sync_strava_for_user'),
        ]
        started = [p.start() for p in self._patchers]
        self._mock_sync = started[-1]

        self._profile, self._activities = _load_coaching_data('user-123', MagicMock())

    def teardown_method(self) -> None:
        for p in self._patchers:
            p.stop()

    def test_strava_sync_is_called(self) -> None:
        self._mock_sync.assert_called_once()

    def test_returns_profile_from_repo(self) -> None:
        assert self._profile is self._mock_profile_repo.load.return_value

    def test_returns_activities_from_repo(self) -> None:
        assert self._activities is self._mock_activity_repo.list_all.return_value
