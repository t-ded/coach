from typing import Optional

from coach.domain.training_analytics import ActiveTrainingPhase
from coach.domain.training_analytics import TrainingMacroPhase
from coach.reasoning.coach.sections.base import ContextSection

_FOCUS_BY_PHASE: dict[TrainingMacroPhase, str] = {
    TrainingMacroPhase.BASE: 'Focus: Build aerobic base with mostly easy volume. Introduce progressive overload gradually.',
    TrainingMacroPhase.BUILD: 'Focus: Increase specificity. Add goal-pace work and race-specific sessions alongside easy volume.',
    TrainingMacroPhase.PEAK: 'Focus: Race-specific intensity at full volume. Quality over quantity — nail key sessions.',
    TrainingMacroPhase.TAPER: 'Focus: Reduce volume 20-30%, maintain workout intensity, prioritize recovery and sleep.',
    TrainingMacroPhase.RACE_WEEK: 'Focus: Minimal volume, race-pace strides only. Prioritize sleep, nutrition, and confidence.',
}


class TrainingPhaseSection(ContextSection):
    def __init__(self, phase: ActiveTrainingPhase) -> None:
        self._phase = phase

    @property
    def header(self) -> str:
        return 'Training phase:'

    def render(self) -> Optional[str]:
        if self._phase.phase == TrainingMacroPhase.OPEN:
            return 'Open training — no active goal with a future date set.'

        weeks_to_goal = self._phase.weeks_to_goal
        goal_name = self._phase.goal_name
        phase_name = self._phase.phase.value

        phase_line = f'Phase: {phase_name} (towards {goal_name}, {weeks_to_goal} week{"s" if weeks_to_goal != 1 else ""} to goal)'
        focus_line = _FOCUS_BY_PHASE[self._phase.phase]

        return f'{phase_line}\n{focus_line}'
