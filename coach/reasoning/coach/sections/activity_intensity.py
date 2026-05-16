from __future__ import annotations

from datetime import datetime
from typing import Optional

from coach.domain.activity_intensity import ActivityIntensityProfile
from coach.domain.activity_intensity import ZoneDistribution
from coach.reasoning.coach.sections.base import ContextSection


def _render_zone_breakdown(zone_distribution: list[ZoneDistribution], total_distance: float) -> str:
    parts = []
    for zd in zone_distribution:
        pct = int(round(100 * zd.distance_meters / total_distance)) if total_distance > 0 else 0
        parts.append(f'{zd.zone.value} {pct}%')
    return ', '.join(parts)


class ActivityIntensitySection(ContextSection):
    def __init__(self, profiles: list[tuple[datetime, str, ActivityIntensityProfile]]) -> None:
        self._profiles = profiles

    @property
    def header(self) -> str:
        return 'Activity intensity breakdown:'

    def render(self) -> Optional[str]:
        if not self._profiles:
            return None

        lines: list[str] = ['-' * 40, 'Pace zone breakdown for recent runs (derived from PBs):']
        for start_time, name, profile in self._profiles:
            total_distance = sum(z.distance_meters for z in profile.zone_distribution)
            zone_str = _render_zone_breakdown(profile.zone_distribution, total_distance)
            date_str = start_time.strftime('%a %d %b')
            activity_label = name or 'Run'
            line = f'{date_str} — {activity_label}: {zone_str}'
            if profile.flags[1:]:
                line += ' | ' + '; '.join(profile.flags[1:])
            lines.append(line)
        lines.append('-' * 40)
        return '\n'.join(lines)
