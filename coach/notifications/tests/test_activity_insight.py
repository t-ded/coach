from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.notifications.activity_insight import ActivityInsightGenerator
from coach.notifications.activity_insight import _format_activity
from coach.notifications.activity_insight import _format_pace
from coach.reasoning.providers import LLMProvider

_BASE_ACTIVITY = Activity(
    id=1,
    sport_type=SportType.RUN,
    name='Morning run',
    start_time_utc=datetime(2026, 5, 14, 7, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=3600,
    moving_time_seconds=3540,
    distance_meters=10_000,
    is_manual=False,
    is_race=False,
)


class TestFormatPace:
    def test_returns_pace_for_run(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            moving_time_seconds=3000,
            distance_meters=10_000,
            is_manual=False,
            is_race=False,
        )
        result = _format_pace(activity)
        assert result == '5:00/km'

    def test_returns_none_for_ride(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RIDE,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            moving_time_seconds=3000,
            distance_meters=30_000,
            is_manual=False,
            is_race=False,
        )
        assert _format_pace(activity) is None

    def test_returns_none_when_no_distance(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            is_manual=False,
            is_race=False,
        )
        assert _format_pace(activity) is None

    def test_returns_none_when_no_moving_time(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            distance_meters=10_000,
            is_manual=False,
            is_race=False,
        )
        assert _format_pace(activity) is None


class TestFormatActivity:
    def test_includes_sport_type_and_distance(self) -> None:
        result = _format_activity(_BASE_ACTIVITY)
        assert 'Run' in result
        assert '10.00 km' in result

    def test_includes_average_pace_for_run(self) -> None:
        result = _format_activity(_BASE_ACTIVITY)
        assert '/km' in result

    def test_includes_heart_rate_when_present(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            average_heart_rate=155.0,
            max_heart_rate=175.0,
            is_manual=False,
            is_race=False,
        )
        result = _format_activity(activity)
        assert '155 bpm' in result
        assert '175 bpm' in result

    def test_omits_heart_rate_when_absent(self) -> None:
        result = _format_activity(_BASE_ACTIVITY)
        assert 'bpm' not in result

    def test_includes_notes_when_present(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name=None,
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=3600,
            notes='Felt tired but pushed through',
            is_manual=False,
            is_race=False,
        )
        result = _format_activity(activity)
        assert 'Felt tired but pushed through' in result

    def test_marks_race_activities(self) -> None:
        activity = Activity(
            id=1,
            sport_type=SportType.RUN,
            name='Parkrun',
            start_time_utc=datetime(2026, 5, 14, tzinfo=UTC),
            elapsed_time_seconds=1500,
            is_manual=False,
            is_race=True,
        )
        result = _format_activity(activity)
        assert 'race' in result


class TestActivityInsightGenerator:
    def setup_method(self) -> None:
        self._mock_client = MagicMock()
        self._mock_client.complete.return_value = 'Great run today!'
        self._client_patcher = patch('coach.notifications.activity_insight.create_llm_client', return_value=self._mock_client)
        self._client_patcher.start()
        self._generator = ActivityInsightGenerator(provider=LLMProvider.GOOGLE, api_key='test-key')

    def teardown_method(self) -> None:
        self._client_patcher.stop()

    def test_generate_calls_llm_and_returns_response(self) -> None:
        result = self._generator.generate(_BASE_ACTIVITY, 'Tom')
        assert result == 'Great run today!'
        self._mock_client.complete.assert_called_once()

    def test_prompt_includes_display_name(self) -> None:
        self._generator.generate(_BASE_ACTIVITY, 'Tom')
        prompt = self._mock_client.complete.call_args[0][0]
        assert 'Tom' in prompt

    def test_prompt_includes_activity_details(self) -> None:
        self._generator.generate(_BASE_ACTIVITY, 'Tom')
        prompt = self._mock_client.complete.call_args[0][0]
        assert 'Run' in prompt
        assert '10.00 km' in prompt
