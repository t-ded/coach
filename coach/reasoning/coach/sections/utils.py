from datetime import UTC
from datetime import date
from datetime import datetime
from typing import Optional


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


def weeks_and_days_until(future_date: date) -> str:
    now = datetime.now(tz=UTC).date()
    days_until = (future_date - now).days
    if days_until <= 0:
        return ''

    weeks_until = days_until // 7
    and_days = days_until % 7

    full_response: list[str] = []
    if weeks_until > 0:
        full_response.append(f'{weeks_until} week{"s" if weeks_until > 1 else ""}')
    if and_days > 0:
        full_response.append(f'{and_days} day{"s" if and_days > 1 else ""}')

    return ' and '.join(full_response)


def combine_sections(sections: list[tuple[str, Optional[str]]]) -> list[str]:
    return [f'{title}\n{content.strip()}' for title, content in sections if content]
