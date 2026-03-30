from typing import Optional

from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.reasoning.coach.sections.base import ContextSection
from coach.reasoning.coach.sections.utils import days_ago


class PersonalBestsSection(ContextSection):
    def __init__(self, running_pbs: RunningPersonalBestsSummary) -> None:
        self._running_pbs = running_pbs

    @property
    def header(self) -> str:
        return 'Running PBs:'

    def render(self) -> Optional[str]:
        pb_fields = [
            ('1K', self._running_pbs.PB_1K),
            ('5K', self._running_pbs.PB_5K),
            ('10K', self._running_pbs.PB_10K),
            ('15K', self._running_pbs.PB_15K),
            ('Half Marathon', self._running_pbs.PB_HALF_MARATHON),
            ('Marathon', self._running_pbs.PB_MARATHON),
        ]

        lines: list[str] = ['-' * 40, 'Running personal bests:']
        for label, pb in pb_fields:
            if pb is not None:
                num_days_ago = days_ago(pb.achieved_on)
                days_ago_suffix = f' ({num_days_ago} day{"" if num_days_ago == 1 else "s"} ago)'
                lines.append(f'- {label}: {pb.pace_str} on {pb.achieved_on}{days_ago_suffix}')
            else:
                lines.append(f'- {label}: No PB recorded')

        lines.append('-' * 40)
        return '\n'.join(lines)
