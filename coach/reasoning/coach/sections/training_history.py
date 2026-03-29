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
from coach.utils import format_total_seconds
from coach.utils import parse_distance_km


def _optional_append(value: Optional[int | float | str], format_str: str, lines: list[str]) -> None:
    if value:
        lines.append(format_str.format(value))


def _format_pace(distance_meters: float, duration_seconds: int) -> str:
    pace_seconds_per_km = duration_seconds / (distance_meters / 1000)
    minutes = int(pace_seconds_per_km) // 60
    seconds = int(pace_seconds_per_km) % 60
    return f'{minutes}:{seconds:02d}/km'


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
            lines.append(self._render_activity_volume(volume, sport))
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

    def _render_activity_summary(self, activity_summary: ActivitySummary) -> str:
        is_distance = activity_summary.sport_type in DISTANCE_SPORT_TYPES
        lines: list[str] = []
        lines.append(f'{activity_summary.sport_type.value}: {activity_summary.description}')
        lines.append(f'- Duration: {format_total_seconds(total_seconds=activity_summary.duration_seconds)}')
        if is_distance:
            _optional_append(parse_distance_km(meters=activity_summary.distance_meters, decimals=1), '- Distance: {}', lines)
            if activity_summary.distance_meters and activity_summary.duration_seconds:
                lines.append(f'- Pace: {_format_pace(activity_summary.distance_meters, activity_summary.duration_seconds)}')
            _optional_append(activity_summary.elevation_gain_meters, '- Elevation gain: {} meters', lines)
        _optional_append(activity_summary.average_heart_rate, '- Average heart rate: {} bpm', lines)
        return '\n'.join(lines)

    def _render_activity_volume(self, volume: ActivityVolume, sport: SportType) -> str:
        lines: list[str] = []
        lines.append(f'- Num activities: {volume.num_activities}')
        lines.append(f'- Total duration: {format_total_seconds(total_seconds=volume.duration_seconds)}')
        if sport in DISTANCE_SPORT_TYPES:
            _optional_append(parse_distance_km(meters=volume.distance_meters, decimals=1), '- Total distance: {}', lines)
        return '\n'.join(lines)
