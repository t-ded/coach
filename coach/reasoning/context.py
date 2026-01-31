from typing import Optional
from typing import cast

from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.utils import format_total_seconds
from coach.utils import parse_distance_km


def _optional_append(value: Optional[int | float | str], format_str: str, lines: list[str]) -> None:
    if value:
        lines.append(format_str.format(value))


def render_activity_volume(volume: ActivityVolume) -> str:
    lines: list[str] = []
    lines.append(f'- Num activities: {volume.num_activities}')
    lines.append(f'- Total duration: {format_total_seconds(total_seconds=volume.duration_seconds)}')
    _optional_append(parse_distance_km(meters=volume.distance_meters, decimals=1), '- Total distance: {}', lines)
    return '\n'.join(lines)


def render_activity_summary(activity_summary: ActivitySummary) -> str:
    lines: list[str] = []
    lines.append(f'{activity_summary.sport_type.value}: {activity_summary.description}')
    lines.append(f'- Duration: {format_total_seconds(total_seconds=activity_summary.duration_seconds)}')
    _optional_append(parse_distance_km(meters=activity_summary.distance_meters, decimals=1), '- Distance: {}', lines)
    _optional_append(activity_summary.elevation_gain_meters, '- Elevation gain: {} meters', lines)
    _optional_append(activity_summary.average_heart_rate, '- Average heart rate: {} bpm', lines)
    return '\n'.join(lines)


def render_weekly_activities(weekly_activities: WeeklyActivities) -> str:
    lines: list[str] = []
    for day, activities in weekly_activities.items():
        activities = cast(list[ActivitySummary], activities)
        if activities:
            lines.append(f'--- {day} ---')
            for activity in activities:
                lines.append(render_activity_summary(activity))
                lines.append('')
    return '\n'.join(lines)


def render_weekly_summary(weekly_summary: WeeklySummary) -> str:
    lines: list[str] = []
    lines.append(f'Weekly summary for {weekly_summary.week_start} to {weekly_summary.week_end}:')
    lines.append('----- Per-day breakdown -----')
    lines.append(render_weekly_activities(weekly_summary.activity_summaries))
    lines.append('----- Volume aggregation by sport -----')
    for sport, volume in weekly_summary.volume_by_sport.items():
        lines.append(f'--- {sport.value} ---')
        lines.append(render_activity_volume(volume=volume))
        lines.append('')
    return '\n'.join(lines)


def render_recent_training_history(recent_training_history: RecentTrainingHistory) -> str:
    lines: list[str] = []
    lines.append('Summary of recent training history:')
    lines.append('-' * 40)

    num_history_weeks = len(recent_training_history.history_weekly_summaries)
    for i, summary in enumerate(reversed(recent_training_history.history_weekly_summaries)):
        weeks_before = num_history_weeks - i
        lines.append(f"{weeks_before} week{'' if weeks_before == 1 else 's'} before current week:")
        lines.append(render_weekly_summary(summary))

    lines.append('-' * 40)
    lines.append('')
    lines.append(f'Current week summary (today is {recent_training_history.generated_at.strftime('%A')}):')
    lines.append(render_weekly_summary(recent_training_history.current_week_summary))

    return '\n'.join(lines)
