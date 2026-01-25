from datetime import date

from coach.builders.weekly_summary import build_weekly_summary
from coach.domain.models import ActivitySummary
from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.tests.utils_for_tests import SAMPLE_RIDE
from coach.tests.utils_for_tests import SAMPLE_RUN


class TestBuildWeeklySummary:
    def setup_method(self) -> None:
        self._activities = [SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]

    def test_date_within_week(self) -> None:
        date_within_week = date(2025, 1, 1)
        summary = build_weekly_summary(self._activities, date_within_week)

        assert summary.week_start == date(2024, 12, 30)
        assert summary.week_end == date(2025, 1, 5)
        assert summary.volume_by_sport == {
            SportType.RUN: ActivityVolume(distance_meters=20_000.0, duration_seconds=7_000, num_activities=2),
            SportType.RIDE: ActivityVolume(distance_meters=20_000.0, duration_seconds=3_500, num_activities=1),
        }
        assert summary.activity_summaries == {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [ActivitySummary.from_activity(SAMPLE_RUN), ActivitySummary.from_activity(SAMPLE_RUN)],
            'Thursday': [ActivitySummary.from_activity(SAMPLE_RIDE)],
            'Friday': [],
            'Saturday': [],
            'Sunday': [],
        }

    def test_date_outside_week(self) -> None:
        date_outside_week = date(2026, 1, 25)
        summary = build_weekly_summary(self._activities, date_outside_week)

        assert summary.week_start == date(2026, 1, 19)
        assert summary.week_end == date(2026, 1, 25)
        assert summary.volume_by_sport == {}
        assert summary.activity_summaries == {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [],
            'Saturday': [],
            'Sunday': [],
        }
