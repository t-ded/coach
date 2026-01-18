from datetime import UTC
from datetime import datetime


def parse_utc_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.astimezone(UTC)
