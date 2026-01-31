from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

from coach.utils import build_sqlite_where_clause
from coach.utils import days_ago
from coach.utils import format_total_seconds
from coach.utils import parse_distance_km
from coach.utils import parse_file
from coach.utils import parse_private_notes_activity_summary
from coach.utils import parse_utc_datetime


def test_parse_utc_datetime() -> None:
    assert parse_utc_datetime('2024-01-01T12:00:00Z') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_utc_datetime('2024-01-01T12:00:00+00:00') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_utc_datetime('2024-01-01T14:00:00+02:00') == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_parse_duration() -> None:
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


def test_parse_file_non_existent() -> None:
    non_existing_path = Path('non_existing_file_xyz123.txt')
    assert parse_file(non_existing_path) is None


def test_parse_file_existent() -> None:
    with NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
        temp_file.write('  test content  \n')
        temp_path = Path(temp_file.name)

    try:
        assert parse_file(temp_path) == 'test content'
    finally:
        temp_path.unlink()


def test_parse_private_notes_activity_summary() -> None:
    assert parse_private_notes_activity_summary('$Summary: Good progress overall.$') == 'Summary: Good progress overall.'
    assert parse_private_notes_activity_summary('$Smthng') == ''
    assert parse_private_notes_activity_summary('Smthng$') == ''
    assert parse_private_notes_activity_summary(None) == ''


class TestBuildSqliteWhereClause:
    def test_no_conditions(self) -> None:
        query, params = build_sqlite_where_clause('SELECT * FROM activities', {})
        assert query == 'SELECT * FROM activities'
        assert params == []

    def test_single_condition(self) -> None:
        query, params = build_sqlite_where_clause('SELECT * FROM activities', {'sport_type': [('=', 'Run')]})
        assert query == 'SELECT * FROM activities WHERE sport_type = ?'
        assert params == ['Run']

    def test_multiple_conditions_different_columns(self) -> None:
        query, params = build_sqlite_where_clause(
            'SELECT * FROM activities',
            {
                'sport_type': [('=', 'Run')],
                'distance': [('>', 5000)],
            },
        )
        assert query == 'SELECT * FROM activities WHERE sport_type = ? AND distance > ?'
        assert params == ['Run', 5000]

    def test_multiple_conditions_same_column(self) -> None:
        query, params = build_sqlite_where_clause(
            'SELECT * FROM activities',
            {
                'distance': [('>', 1000), ('<', 10000)],
            },
        )
        assert query == 'SELECT * FROM activities WHERE distance > ? AND distance < ?'
        assert params == [1000, 10000]

    def test_none_values(self) -> None:
        query, params = build_sqlite_where_clause(
            'SELECT * FROM activities',
            {
                'sport_type': [('=', 'Run')],
                'distance': [('>', None)],
            },
        )
        assert query == 'SELECT * FROM activities WHERE sport_type = ?'
        assert params == ['Run']
