from typing import Optional
from typing import cast

from coach.domain.activity import DISTANCE_SPORT_TYPES
from coach.domain.activity import SportType
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.reasoning.coach.sections.base import ContextSection
from coach.reasoning.coach.sections.utils import format_total_seconds
from coach.reasoning.coach.sections.utils import parse_distance_km


def _optional_append(value: Optional[int | float | str], format_str: str, lines: list[str]) -> None:
    if value:
        lines.append(format_str.format(value))


def _format_pace(distance_meters: float, duration_seconds: int) -> str:
    pace_seconds_per_km = duration_seconds / (distance_meters / 1000)
    minutes = int(pace_seconds_per_km) // 60
    seconds = int(pace_seconds_per_km) % 60
    return f'{minutes}:{seconds:02d}/km'


def _render_time(activity_summary: ActivitySummary, active_seconds: int, has_rest: bool) -> str:
    if has_rest:
        rest_seconds = activity_summary.elapsed_time_seconds - active_seconds
        active_line = f'- Active time: {format_total_seconds(total_seconds=active_seconds)}'
        elapsed_line = f'- Elapsed time: {format_total_seconds(total_seconds=activity_summary.elapsed_time_seconds)} (rest: {format_total_seconds(total_seconds=rest_seconds)})'
        return f'{active_line}\n{elapsed_line}'
    return f'- Moving time: {format_total_seconds(total_seconds=active_seconds)} (no rest)'


def _render_pace(activity_summary: ActivitySummary, active_seconds: int, has_rest: bool) -> Optional[str]:
    if not activity_summary.distance_meters or not active_seconds:
        return None
    active_pace = _format_pace(activity_summary.distance_meters, active_seconds)
    if has_rest:
        elapsed_pace = _format_pace(activity_summary.distance_meters, activity_summary.elapsed_time_seconds)
        pace_str = f'- Active pace: {active_pace}'
        if elapsed_pace != active_pace:
            pace_str += f'\n- Elapsed pace: {elapsed_pace}'
        return pace_str
    return f'- Pace: {active_pace}'


class TrainingHistorySection(ContextSection):
    def __init__(self, recent_training_history: RecentTrainingHistory) -> None:
        self._history = recent_training_history

    @property
    def header(self) -> str:
        return 'Recent weeks training context:'

    def render(self) -> Optional[str]:
        lines: list[str] = []
        lines.append('Summary of recent training history:')
        lines.append('-' * 40)

        num_history_weeks = len(self._history.history_weekly_summaries)
        for i, summary in enumerate(reversed(self._history.history_weekly_summaries)):
            weeks_before = num_history_weeks - i
            lines.append(f'{weeks_before} week{"" if weeks_before == 1 else "s"} before current week:')
            lines.append(self._render_weekly_summary(summary))

        lines.append('-' * 40)
        lines.append('')
        lines.append(f'Current week summary (today is {self._history.generated_at.strftime("%A")}):')
        lines.append(self._render_weekly_summary(self._history.current_week_summary))

        return '\n'.join(lines)

    def _render_weekly_summary(self, weekly_summary: WeeklySummary) -> str:
        lines: list[str] = []
        lines.append(f'Weekly summary for {weekly_summary.week_start} to {weekly_summary.week_end}:')
        lines.append('----- Per-day breakdown -----')
        lines.append(self._render_weekly_activities(weekly_summary.activity_summaries))
        lines.append('----- Volume aggregation by sport -----')
        for sport, volume in weekly_summary.volume_by_sport.items():
            lines.append(f'--- {sport.value} ---')
            lines.append(self._render_activity_volume(volume=volume, sport=sport))
            lines.append('')
        return '\n'.join(lines)

    def _render_weekly_activities(self, weekly_activities: WeeklyActivities) -> str:
        lines: list[str] = []
        for day, activities in weekly_activities.items():
            activities = cast(list[ActivitySummary], activities)
            if activities:
                lines.append(f'--- {day} ---')
                for activity in activities:
                    lines.append(self._render_activity_summary(activity))
                    lines.append('')
        return '\n'.join(lines)

    @staticmethod
    def _render_activity_summary(activity_summary: ActivitySummary) -> str:
        is_distance = activity_summary.sport_type in DISTANCE_SPORT_TYPES
        active_seconds = activity_summary.moving_time_seconds or activity_summary.elapsed_time_seconds
        has_rest = (
            activity_summary.moving_time_seconds is not None
            and activity_summary.moving_time_seconds < activity_summary.elapsed_time_seconds
        )

        lines: list[str] = []
        lines.append(f'{activity_summary.sport_type.value}: {activity_summary.description}')
        lines.append(_render_time(activity_summary, active_seconds, has_rest))
        if is_distance:
            distance_km = parse_distance_km(meters=activity_summary.distance_meters, decimals=1)
            _optional_append(distance_km, '- Distance: {}', lines)

            pace = _render_pace(activity_summary, active_seconds, has_rest)
            _optional_append(pace, '{}', lines)

            _optional_append(activity_summary.elevation_gain_meters, '- Elevation gain: {} meters', lines)
        _optional_append(activity_summary.average_heart_rate, '- Average heart rate: {} bpm', lines)
        _optional_append(activity_summary.max_heart_rate, '- Max heart rate: {} bpm', lines)
        return '\n'.join(lines)

    @staticmethod
    def _render_activity_volume(*, volume: ActivityVolume, sport: SportType) -> str:
        lines: list[str] = []
        lines.append(f'- Num activities: {volume.num_activities}')
        lines.append(f'- Total duration: {format_total_seconds(total_seconds=volume.duration_seconds)}')
        if sport in DISTANCE_SPORT_TYPES:
            distance_km = parse_distance_km(meters=volume.distance_meters, decimals=1)
            _optional_append(distance_km, '- Total distance: {}', lines)
        return '\n'.join(lines)
