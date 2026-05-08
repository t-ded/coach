from datetime import date
from typing import Optional

from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.reasoning.coach.sections.base import ContextSection
from coach.reasoning.coach.sections.utils import combine_sections
from coach.reasoning.coach.sections.utils import format_total_seconds
from coach.reasoning.coach.sections.utils import parse_distance_km
from coach.reasoning.coach.sections.utils import weeks_and_days_until

PRIORITY_OPTIONS = [prio.value for prio in Priority]


def render_training_goal(training_goal: TrainingGoal) -> str:
    lines: list[str] = []
    lines.append(f'- {training_goal.name}')
    lines.append(f'    - Sport: {training_goal.sport_type.value}')

    time_until_suffix = f' ({weeks_and_days_until(training_goal.goal_date)})' if isinstance(training_goal.goal_date, date) else ''
    lines.append(f'    - Goal date: {training_goal.goal_date}' + time_until_suffix)

    if isinstance(training_goal, DistanceActivityTrainingGoal):
        lines.append(f'    - Distance: {parse_distance_km(meters=training_goal.goal_distance_meters, decimals=4)}')
        lines.append(f'    - Total duration: {format_total_seconds(total_seconds=training_goal.goal_duration_seconds)}')
        lines.append(f'    - Pace: {training_goal.goal_pace}')

    if training_goal.notes:
        lines.append(f'    - Notes: {training_goal.notes}')

    lines.append(f'    - Priority: {training_goal.priority} (Options were: {PRIORITY_OPTIONS})')

    return '\n'.join(lines)


class ProfileSection(ContextSection):
    def __init__(self, profile: UserProfile) -> None:
        self._profile = profile

    @property
    def header(self) -> str:
        return 'User profile:'

    def render(self) -> Optional[str]:
        goals_text = '\n'.join(render_training_goal(g) for g in self._profile.goals) if self._profile.goals else None
        sections: list[tuple[str, Optional[str]]] = [
            ('--- Training preferences ---', self._profile.training_preferences or '(not set)'),
            ('--- Personal information ---', self._profile.personal_information or '(not set)'),
            ('--- Constraints ---', self._profile.constraints or '(not set)'),
            ('--- Goals ---', goals_text or '(not set)'),
        ]
        return '\n\n'.join(combine_sections(sections))
