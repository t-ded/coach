import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Optional

from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import WeeklyActivities


def get_week_start_week_end(center_date: date | datetime) -> tuple[date, date]:
    center_date = center_date.date() if isinstance(center_date, datetime) else center_date
    return (
        center_date - timedelta(days=center_date.weekday()),
        center_date + timedelta(days=(6 - center_date.weekday())),
    )


def get_activities_between_dates(
    activities: Iterable[Activity],
    *,
    window_start: date,
    window_end: date,
) -> list[Activity]:
    return [activity for activity in activities if window_start <= activity.start_time_utc.date() <= window_end]


def create_empty_weekly_activities() -> WeeklyActivities:
    return {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    }


def bucket_activities_by_weekday(activities: Iterable[Activity]) -> WeeklyActivities:
    buckets: WeeklyActivities = create_empty_weekly_activities()

    for activity in activities:
        activity_weekday = activity.start_time_utc.strftime("%A")
        buckets[activity_weekday].append(ActivitySummary.from_activity(activity))  # type: ignore[literal-required]

    return buckets


def categorize_activities_by_sport_type(activities: Iterable[Activity]) -> dict[SportType, list[Activity]]:
    categorized_activities: dict[SportType, list[Activity]] = defaultdict(list)
    for activity in activities:
        categorized_activities[activity.sport_type].append(activity)
    return categorized_activities


def get_categorized_volume(activities: Iterable[Activity]) -> dict[SportType, ActivityVolume]:
    categorized_activities = categorize_activities_by_sport_type(activities)
    return {sport_type: ActivityVolume.from_activities(activities) for sport_type, activities in categorized_activities.items()}


def parse_sport_type(text: str) -> str:
    """Parse sport type from text, handling common variations."""
    text_lower = text.lower().strip()

    sport_map = {
        'run': SportType.RUN,
        'running': SportType.RUN,
        'ride': SportType.RIDE,
        'riding': SportType.RIDE,
        'bike': SportType.RIDE,
        'biking': SportType.RIDE,
        'cycle': SportType.RIDE,
        'cycling': SportType.RIDE,
        'swim': SportType.SWIM,
        'swimming': SportType.SWIM,
        'strength': SportType.STRENGTH,
        'weights': SportType.STRENGTH,
        'weight training': SportType.STRENGTH,
        'weighttraining': SportType.STRENGTH,
        'weight lifting': SportType.STRENGTH,
        'weightlifting': SportType.STRENGTH,
        'walk': SportType.WALK,
        'walking': SportType.WALK,
    }

    return sport_map.get(text_lower, SportType.OTHER)


def parse_distance(text: str) -> Optional[float]:
    """Parse distance from text, supporting km, mi, m formats."""
    patterns = [
        (r'(\d+\.?\d*)\s*km', 1000),
        (r'(\d+\.?\d*)\s*mi(?:les?)?', 1609.34),
        (r'(\d+\.?\d*)\s*m(?:eters?)?(?!\s*i)', 1),
    ]

    text_lower = text.lower()
    for pattern, multiplier in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1)) * multiplier

    return None


def parse_duration(text: str) -> Optional[int]:
    """Parse duration from text, supporting HH:MM:SS, MM:SS, or descriptive formats."""
    time_match = re.search(r"(\d+):(\d+)(?::(\d+))?", text)
    if time_match:
        hours = int(time_match.group(1)) if time_match.group(3) else 0
        minutes = int(time_match.group(2)) if time_match.group(3) else int(time_match.group(1))
        seconds = int(time_match.group(3)) if time_match.group(3) else int(time_match.group(2))
        return hours * 3600 + minutes * 60 + seconds

    descriptive_patterns = [
        (r'(\d+\.?\d*)\s*h(?:ours?)?', 3600),
        (r'(\d+\.?\d*)\s*min(?:utes?)?', 60),
        (r'(\d+\.?\d*)\s*s(?:ec(?:onds?)?)?', 1),
    ]

    text_lower = text.lower()
    total_seconds = 0.0
    for pattern, multiplier in descriptive_patterns:
        match = re.search(pattern, text_lower)
        if match:
            total_seconds += float(match.group(1)) * multiplier

    return int(total_seconds) if total_seconds > 0 else None


def parse_pace(text: str) -> Optional[str]:
    """Parse pace from text, supporting min/km, min/mi formats."""
    pace_match = re.search(r'(\d+:\d+)\s*(?:/|per)\s*(km|mi)', text.lower())
    if pace_match:
        pace_value = pace_match.group(1)
        unit = pace_match.group(2)
        return f'{pace_value}/{unit}'

    return None


def parse_date(text: str) -> str | date:
    """
    Parse date from text, supporting various formats.

    Returns:
        - date object if a valid date is found and parsed
        - original text string if no date pattern matches
    """
    date_patterns = [
        (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d'),  # 2025-03-15
        (r'\d{4}/\d{2}/\d{2}', '%Y/%m/%d'),  # 2025/03/15
        (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),  # 15/03/2025
        (r'\d{1,2}/\d{1,2}/\d{4}', '%d/%m/%Y'),  # 15/3/2025
        (r'\d{1,2}.\d{1,2}.\d{4}', '%d.%m.%Y'),  # 15.3.2025
        (r'\d{1,2}. \d{1,2}. \d{4}', '%d. %m. %Y'),  # 15. 3. 2025
        (r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', '%d %B %Y'),  # 15 March 2025
        (r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}', '%B %d, %Y'),  # March 15, 2025
    ]

    for pattern, date_format in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(0)
            try:
                parsed_date = datetime.strptime(date_str, date_format).replace(tzinfo=UTC).date()
                return parsed_date
            except ValueError:
                continue

    return text
