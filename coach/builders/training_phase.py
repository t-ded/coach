from datetime import date
from datetime import datetime

from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.training_analytics import ActiveTrainingPhase
from coach.domain.training_analytics import TrainingMacroPhase

_PRIORITY_ORDER: dict[Priority, int] = {
    Priority.VERY_HIGH: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


def _goal_date_as_date(g: TrainingGoal) -> date:
    if not isinstance(g.goal_date, date):
        raise TypeError(f'Expected date, got {type(g.goal_date)}')
    return g.goal_date


def detect_training_phase(goals: tuple[TrainingGoal, ...], generated_at: datetime) -> ActiveTrainingPhase:
    today = generated_at.date()

    future_goals = [g for g in goals if isinstance(g.goal_date, date) and (g.goal_date - today).days >= 0]

    if not future_goals:
        return ActiveTrainingPhase(phase=TrainingMacroPhase.OPEN, weeks_to_goal=None, goal_name=None)

    # Sort by priority (highest first), then by proximity (soonest first)
    primary = sorted(future_goals, key=lambda g: (_PRIORITY_ORDER[g.priority], (_goal_date_as_date(g) - today).days))[0]

    days_to_goal = (_goal_date_as_date(primary) - today).days

    if days_to_goal <= 7:
        phase = TrainingMacroPhase.RACE_WEEK
    elif days_to_goal <= 21:
        phase = TrainingMacroPhase.TAPER
    elif days_to_goal <= 56:
        phase = TrainingMacroPhase.PEAK
    elif days_to_goal <= 112:
        phase = TrainingMacroPhase.BUILD
    else:
        phase = TrainingMacroPhase.BASE

    weeks_to_goal = days_to_goal // 7

    return ActiveTrainingPhase(phase=phase, weeks_to_goal=weeks_to_goal, goal_name=primary.name)
