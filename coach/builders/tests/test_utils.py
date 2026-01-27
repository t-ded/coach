from datetime import UTC
from datetime import date
from datetime import datetime

from coach.builders.utils import bucket_activities_by_weekday
from coach.builders.utils import categorize_activities_by_sport_type
from coach.builders.utils import get_activities_between_dates
from coach.builders.utils import get_categorized_volume
from coach.builders.utils import get_week_start_week_end
from coach.builders.utils import parse_date
from coach.builders.utils import parse_distance
from coach.builders.utils import parse_duration
from coach.builders.utils import parse_pace
from coach.builders.utils import parse_sport_type
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


def test_parse_sport_type() -> None:
    assert parse_sport_type('Run') == SportType.RUN
    assert parse_sport_type('run') == SportType.RUN
    assert parse_sport_type('running') == SportType.RUN

    assert parse_sport_type('Gibberish') == SportType.OTHER


def test_parse_distance() -> None:
    assert parse_distance('21.0975 km') == 21_097.5
    assert parse_distance('21.0975 kms') == 21_097.5
    assert parse_distance('20000 m') == 20_000.0
    assert parse_distance('20000 meters') == 20_000.0
    assert parse_distance('1 mile') == 1_609.34
    assert parse_distance('2 miles') == 2 * 1_609.34
    assert parse_distance('Gibberish') is None


def test_parse_duration() -> None:
    assert parse_duration('01:00:00') == 3_600
    assert parse_duration('01:01:05') == 3_665
    assert parse_duration('01:05') == 65
    assert parse_duration('1 minute 30 seconds') == 90
    assert parse_duration('1 hour 30 minutes') == 5_400
    assert parse_duration('Gibberish') is None


def test_parse_pace() -> None:
    assert parse_pace('4:30/km') == '4:30/km'
    assert parse_pace('4:30 per km') == '4:30/km'
    assert parse_pace('7:00/mi') == '7:00/mi'
    assert parse_pace('7:00 per mi') == '7:00/mi'
    assert parse_pace('Gibberish') is None


def test_parse_date() -> None:
    assert parse_date('2024-01-30') == date(2024, 1, 30)
    assert parse_date('2024/01/30') == date(2024, 1, 30)
    assert parse_date('30/01/2024') == date(2024, 1, 30)
    assert parse_date('30/1/2024') == date(2024, 1, 30)
    assert parse_date('30.1.2024') == date(2024, 1, 30)
    assert parse_date('30. 1. 2024') == date(2024, 1, 30)
    assert parse_date('30 January 2024') == date(2024, 1, 30)
    assert parse_date('January 30, 2024') == date(2024, 1, 30)
