from datetime import UTC
from datetime import date
from datetime import datetime


def parse_utc_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.astimezone(UTC)


def days_ago(past_date: date | datetime) -> int:
    now = datetime.now(tz=UTC) if isinstance(past_date, datetime) else datetime.now(tz=UTC).date()
    return (now - past_date).days
