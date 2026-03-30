from datetime import UTC
from datetime import datetime
from typing import Optional


def parse_utc_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.astimezone(UTC)


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
