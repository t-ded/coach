from datetime import UTC
from datetime import date
from datetime import datetime

from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.models import ActivitySummary
from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import WeeklySummary
from coach.tests.utils_for_tests import SAMPLE_RIDE
from coach.tests.utils_for_tests import SAMPLE_RUN


class TestBuildRecentTrainingHistory:
    def setup_method(self) -> None:
        self._activities = [SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]

    @staticmethod
    def _create_empty_weekly_summary(week_start: date, week_end: date) -> WeeklySummary:
        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            volume_by_sport={},
            activity_summaries={
                'Monday': [],
                'Tuesday': [],
                'Wednesday': [],
                'Thursday': [],
                'Friday': [],
                'Saturday': [],
                'Sunday': [],
            },
        )

    @staticmethod
    def _create_inclusive_weekly_summary() -> WeeklySummary:
        return WeeklySummary(
            week_start=date(2024, 12, 30),
            week_end=date(2025, 1, 5),
            volume_by_sport={
                SportType.RUN: ActivityVolume(distance_meters=20_000.0, duration_seconds=7_000, num_activities=2),
                SportType.RIDE: ActivityVolume(distance_meters=20_000.0, duration_seconds=3_500, num_activities=1),
            },
            activity_summaries={
                'Monday': [],
                'Tuesday': [],
                'Wednesday': [ActivitySummary.from_activity(SAMPLE_RUN), ActivitySummary.from_activity(SAMPLE_RUN)],
                'Thursday': [ActivitySummary.from_activity(SAMPLE_RIDE)],
                'Friday': [],
                'Saturday': [],
                'Sunday': [],
            },
        )

    def test_current_week_no_history(self) -> None:
        datetime_within_week = datetime(2025, 1, 1, tzinfo=UTC)
        history = build_recent_training_history(self._activities, generated_at=datetime_within_week, num_history_weeks=0)

        assert history.generated_at == datetime_within_week
        assert history.current_week_summary == self._create_inclusive_weekly_summary()
        assert history.history_weekly_summaries == ()

    def test_one_past_week(self) -> None:
        datetime_one_week_in_future = datetime(2025, 1, 8, tzinfo=UTC)
        week_start = date(2025, 1, 6)
        week_end = date(2025, 1, 12)
        history = build_recent_training_history(self._activities, generated_at=datetime_one_week_in_future, num_history_weeks=1)

        assert history.generated_at == datetime_one_week_in_future
        assert history.current_week_summary == self._create_empty_weekly_summary(week_start, week_end)
        assert history.history_weekly_summaries == (self._create_inclusive_weekly_summary(), )

    def test_two_past_weeks(self) -> None:
        datetime_two_weeks_in_future = datetime(2025, 1, 15, tzinfo=UTC)
        week_start = date(2025, 1, 13)
        week_end = date(2025, 1, 19)
        previous_week_start = date(2025, 1, 6)
        previous_week_end = date(2025, 1, 12)
        history = build_recent_training_history(self._activities, generated_at=datetime_two_weeks_in_future, num_history_weeks=2)

        assert history.generated_at == datetime_two_weeks_in_future
        assert history.current_week_summary == self._create_empty_weekly_summary(week_start, week_end)
        assert history.history_weekly_summaries == (
            self._create_empty_weekly_summary(previous_week_start, previous_week_end),
            self._create_inclusive_weekly_summary(),
        )
