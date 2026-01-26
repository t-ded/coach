from datetime import UTC
from datetime import date
from datetime import datetime

from coach.builders.utils import bucket_activities_by_weekday
from coach.builders.utils import categorize_activities_by_sport_type
from coach.builders.utils import get_activities_between_dates
from coach.builders.utils import get_categorized_volume
from coach.builders.utils import get_week_start_week_end
from coach.domain.activity import SportType
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.tests.utils_for_tests import SAMPLE_RIDE
from coach.tests.utils_for_tests import SAMPLE_RUN


def test_get_week_start_week_end() -> None:
    center_date_monday = date(2026, 1, 19)
    center_date_wednesday = datetime(2026, 1, 21, tzinfo=UTC)
    center_date_sunday = date(2026, 1, 25)

    assert get_week_start_week_end(center_date_monday) == (center_date_monday, center_date_sunday)
    assert get_week_start_week_end(center_date_wednesday) == (center_date_monday, center_date_sunday)
    assert get_week_start_week_end(center_date_sunday) == (center_date_monday, center_date_sunday)


def test_get_activities_between_dates() -> None:
    activities = [SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]
    window_start = date(2025, 1, 2)
    window_end = date(2025, 1, 3)

    assert get_activities_between_dates(activities, window_start=window_start, window_end=window_end) == [SAMPLE_RIDE]


def test_bucket_activities_by_weekday() -> None:
    activities = [SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]

    assert bucket_activities_by_weekday(activities) == {
        'Monday': [],
        'Tuesday': [],
        'Wednesday': [ActivitySummary.from_activity(SAMPLE_RUN), ActivitySummary.from_activity(SAMPLE_RUN)],
        'Thursday': [ActivitySummary.from_activity(SAMPLE_RIDE)],
        'Friday': [],
        'Saturday': [],
        'Sunday': [],
    }


def test_categorize_activities_by_sport_type() -> None:
    assert categorize_activities_by_sport_type([SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]) == {SportType.RUN: [SAMPLE_RUN, SAMPLE_RUN], SportType.RIDE: [SAMPLE_RIDE]}


def test_get_categorized_volume() -> None:
    assert get_categorized_volume([SAMPLE_RUN, SAMPLE_RIDE, SAMPLE_RUN]) == {
        SportType.RUN: ActivityVolume(distance_meters=20_000.0, duration_seconds=7_000, num_activities=2),
        SportType.RIDE: ActivityVolume(distance_meters=20_000.0, duration_seconds=3_500, num_activities=1),
    }
