from typing import Optional

from coach.domain.training_analytics import TrainingTrends
from coach.reasoning.coach.sections.base import ContextSection


class TrainingTrendsSection(ContextSection):
    def __init__(self, trends: TrainingTrends) -> None:
        self._trends = trends

    @property
    def header(self) -> str:
        return 'Training trends:'

    def render(self) -> Optional[str]:
        entries = self._trends.weekly_entries
        if not entries:
            return None

        n = len(entries)
        lines: list[str] = [f'Training trends (last {n} week{"s" if n != 1 else ""}):']

        for entry in entries:
            lines.append(
                f'  Week of {entry.week_start}: {entry.running_km} km | {entry.total_duration_hours} h | {entry.session_count} sessions',
            )

        if self._trends.four_week_avg_running_km is not None:
            lines.append(f'4-week avg: {self._trends.four_week_avg_running_km} km/week running')
            lines.append(f'Volume trend: {self._trends.volume_trend}')

        lines.append(f'Active weeks: {self._trends.weeks_active}/{n}')

        if self._trends.longest_run_km is not None:
            lines.append(f'Longest run: {self._trends.longest_run_km} km')

        return '\n'.join(lines)
