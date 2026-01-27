from datetime import UTC
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Optional


def parse_utc_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(UTC)


def format_total_seconds(*, total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'


def parse_distance_km(*, meters: Optional[float], decimals: int = 2) -> Optional[str]:
    if not meters:
        return None
    km = meters / 1000
    return f'{km:.{decimals}f} km'


def days_ago(past_date: date | datetime) -> int:
    now = datetime.now(tz=UTC) if isinstance(past_date, datetime) else datetime.now(tz=UTC).date()
    return (now - past_date).days


def parse_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8').strip()


def parse_private_notes_activity_summary(private_notes: Optional[str]) -> str:
    if not private_notes:
        return ''

    start = private_notes.find('$')
    if start == -1:
        return ''

    end = private_notes.find('$', start + 1)
    if end == -1:
        return ''

    return private_notes[start + 1 : end]


def build_sqlite_where_clause(base_query: str, conditions: dict[str, list[tuple[str, Any]]]) -> tuple[str, list[Any]]:
    """
    Build a SQL query with optional filters.

    Args:
        base_query: The base SQL query (e.g., 'SELECT * FROM table')
        conditions: Dict of {key: (operator, value)}
                   Only non-None values are included.

    Returns:
        Tuple of (query_string, params_list)
    """
    clauses = []
    params = []

    for column, column_conditions in conditions.items():
        for operator, value in column_conditions:
            if value is not None:
                clauses.append(f'{column} {operator} ?')
                params.append(value)

    where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
    query = base_query + where

    return query, params
