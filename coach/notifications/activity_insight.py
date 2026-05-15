from typing import Optional

from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client


class ActivityInsightGenerator:
    def __init__(self, *, provider: LLMProvider, api_key: str) -> None:
        self._client = create_llm_client(provider=provider, api_key=api_key)

    def generate(self, activity: Activity, display_name: str) -> str:
        details = _format_activity(activity)
        prompt = (
            f'You are a personal training coach. Generate a brief, specific, encouraging post-activity message '
            f'for {display_name} based on the following activity:\n\n'
            f'{details}\n\n'
            'Write 3-5 sentences. Reference the real numbers from the activity. '
            'Comment on what was notable — good effort, strong pace, high elevation, etc. '
            'End with brief encouragement or a forward-looking observation. '
            'Do not be generic. Do not invent data not listed above.'
        )
        return self._client.complete(prompt)


def _format_activity(activity: Activity) -> str:
    parts: list[str] = [f'Sport: {activity.sport_type}']

    date_str = activity.start_time_utc.strftime('%A, %B %d')
    parts.append(f'Date: {date_str}')

    if activity.distance_meters:
        km = activity.distance_meters / 1000
        parts.append(f'Distance: {km:.2f} km')
        pace = _format_pace(activity)
        if pace:
            parts.append(f'Average pace: {pace}')

    elapsed_min = activity.elapsed_time_seconds // 60
    parts.append(f'Duration: {elapsed_min} min')

    if activity.average_heart_rate:
        parts.append(f'Average HR: {activity.average_heart_rate:.0f} bpm')
    if activity.max_heart_rate:
        parts.append(f'Max HR: {activity.max_heart_rate:.0f} bpm')
    if activity.elevation_gain_meters:
        parts.append(f'Elevation gain: {activity.elevation_gain_meters:.0f} m')
    if activity.is_race:
        parts.append('Marked as: race')
    if activity.notes:
        parts.append(f'Athlete notes: {activity.notes}')

    return '\n'.join(parts)


def _format_pace(activity: Activity) -> Optional[str]:
    if not activity.distance_meters or not activity.moving_time_seconds:
        return None
    if activity.distance_meters == 0 or activity.sport_type not in (SportType.RUN, SportType.WALK):
        return None
    pace_seconds_per_km = activity.moving_time_seconds / (activity.distance_meters / 1000)
    minutes = int(pace_seconds_per_km // 60)
    seconds = int(pace_seconds_per_km % 60)
    return f'{minutes}:{seconds:02d}/km'
