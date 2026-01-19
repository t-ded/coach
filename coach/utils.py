from datetime import UTC
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_utc_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.astimezone(UTC)


def days_ago(past_date: date | datetime) -> int:
    now = datetime.now(tz=UTC) if isinstance(past_date, datetime) else datetime.now(tz=UTC).date()
    return (now - past_date).days


def parse_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8').strip()
