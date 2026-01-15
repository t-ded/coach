from datetime import UTC
from datetime import datetime

from coach.utils import parse_utc_datetime


def test_parse_utc_datetime() -> None:
    assert parse_utc_datetime('2024-01-01T12:00:00Z') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_utc_datetime('2024-01-01T12:00:00+00:00') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_utc_datetime('2024-01-01T14:00:00+02:00') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
