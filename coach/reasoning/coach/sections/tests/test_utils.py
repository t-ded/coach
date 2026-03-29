from datetime import UTC
from datetime import datetime
from datetime import timedelta

from coach.reasoning.coach.sections.utils import combine_sections
from coach.reasoning.coach.sections.utils import days_ago
from coach.reasoning.coach.sections.utils import format_total_seconds
from coach.reasoning.coach.sections.utils import parse_distance_km
from coach.reasoning.coach.sections.utils import weeks_and_days_until


def test_format_total_seconds() -> None:
    assert format_total_seconds(total_seconds=3600) == '01:00:00'
    assert format_total_seconds(total_seconds=3665) == '01:01:05'
    assert format_total_seconds(total_seconds=65) == '00:01:05'


def test_parse_distance_km() -> None:
    assert parse_distance_km(meters=None, decimals=0) is None
    assert parse_distance_km(meters=500, decimals=2) == '0.50 km'
    assert parse_distance_km(meters=10_000, decimals=0) == '10 km'
    assert parse_distance_km(meters=10_500, decimals=1) == '10.5 km'


def test_days_ago_date() -> None:
    today = datetime.now(tz=UTC).date()

    assert days_ago(today) == 0
    assert days_ago(today - timedelta(days=1)) == 1
    assert days_ago(today - timedelta(days=7)) == 7


def test_days_ago_datetime() -> None:
    now = datetime.now(tz=UTC)

    assert days_ago(now) == 0
    assert days_ago(now - timedelta(days=1)) == 1
    assert days_ago(now - timedelta(days=30)) == 30


def test_weeks_and_days_until() -> None:
    today = datetime.now(tz=UTC).date()

    assert weeks_and_days_until(today) == ''
    assert weeks_and_days_until(today + timedelta(days=1)) == '1 day'
    assert weeks_and_days_until(today + timedelta(days=7)) == '1 week'
    assert weeks_and_days_until(today + timedelta(days=14)) == '2 weeks'
    assert weeks_and_days_until(today + timedelta(days=15)) == '2 weeks and 1 day'
    assert weeks_and_days_until(today + timedelta(days=16)) == '2 weeks and 2 days'


def test_combine_sections_all_present() -> None:
    result = combine_sections([('Title A:', 'content a'), ('Title B:', 'content b')])
    assert result == ['Title A:\ncontent a', 'Title B:\ncontent b']


def test_combine_sections_skips_none() -> None:
    result = combine_sections([('Title A:', 'content a'), ('Title B:', None), ('Title C:', 'content c')])
    assert result == ['Title A:\ncontent a', 'Title C:\ncontent c']


def test_combine_sections_all_none() -> None:
    assert combine_sections([('Title A:', None), ('Title B:', None)]) == []


def test_combine_sections_strips_content() -> None:
    result = combine_sections([('Title:', '  content with whitespace  ')])
    assert result == ['Title:\ncontent with whitespace']
