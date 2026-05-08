from typing import Optional

from coach.domain.training_analytics import PaceZones
from coach.reasoning.coach.sections.base import ContextSection


class PaceZonesSection(ContextSection):
    def __init__(self, pace_zones: Optional[PaceZones]) -> None:
        self._pace_zones = pace_zones

    @property
    def header(self) -> str:
        return 'Training pace zones:'

    def render(self) -> Optional[str]:
        if self._pace_zones is None:
            return None

        lines: list[str] = []
        lines.append(f'Derived from {self._pace_zones.reference_distance} PB:')
        lines.append(f'- Easy: {self._pace_zones.easy_pace}')
        lines.append(f'- Marathon: {self._pace_zones.marathon_pace}')
        lines.append(f'- Threshold: {self._pace_zones.threshold_pace}')
        lines.append(f'- Interval / VO2max: {self._pace_zones.interval_pace}')
        return '\n'.join(lines)
