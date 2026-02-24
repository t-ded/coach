from datetime import date
from typing import Optional
from typing import cast

from coach.builders.training_goal import build_training_goal
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import TrainingGoal
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.utils import days_ago
from coach.utils import format_total_seconds
from coach.utils import parse_distance_km
from coach.utils import weeks_and_days_until


def _optional_append(value: Optional[int | float | str], format_str: str, lines: list[str]) -> None:
    if value:
        lines.append(format_str.format(value))


def render_running_pbs(running_pbs: RunningPersonalBestsSummary) -> str:
    pb_fields = [
        ('1K', running_pbs.PB_1K),
        ('5K', running_pbs.PB_5K),
        ('10K', running_pbs.PB_10K),
        ('15K', running_pbs.PB_15K),
        ('Half Marathon', running_pbs.PB_HALF_MARATHON),
        ('Marathon', running_pbs.PB_MARATHON),
    ]

    lines: list[str] = ['-' * 40, 'Running personal bests:']
    for label, pb in pb_fields:
        if pb is not None:
            num_days_ago = days_ago(pb.DATE)
            days_ago_suffix = f' ({num_days_ago} day{"" if num_days_ago == 1 else "s"} ago)'
            lines.append(f'- {label}: {pb.PACE_STR} on {pb.DATE}{days_ago_suffix}')
        else:
            lines.append(f'- {label}: No PB recorded')

    lines.append('-' * 40)
    return '\n'.join(lines)


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


def render_training_goal(training_goal: TrainingGoal) -> str:
    lines: list[str] = []
    lines.append(f'- {training_goal.name}')
    lines.append(f'    - Sport: {training_goal.sport_type.value}')

    time_until_suffix = f' (in {weeks_and_days_until(training_goal.goal_date)})' if isinstance(training_goal.goal_date, date) else ''
    lines.append(f'    - Goal date: {training_goal.goal_date}' + time_until_suffix)

    if isinstance(training_goal, DistanceActivityTrainingGoal):
        lines.append(f'    - Distance: {parse_distance_km(meters=training_goal.goal_distance_meters, decimals=4)}')
        lines.append(f'    - Total duration: {format_total_seconds(total_seconds=training_goal.goal_duration_seconds)}')
        lines.append(f'    - Pace: {training_goal.goal_pace}')

    if training_goal.notes:
        lines.append(f'    - Notes: {training_goal.notes}')

    return '\n'.join(lines)


def render_system_prompt(system_prompt: Optional[str]) -> Optional[str]:
    if system_prompt is None:
        return None

    parts = system_prompt.split('### Goals:')
    text_lines = parts[0]
    goals = [build_training_goal(goal) for goal in parts[1].split('\n\n')]
    rendered_goals = '\n'.join([render_training_goal(goal) for goal in goals])

    return text_lines + '### Goals:\n' + rendered_goals
