from typing import Optional

from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.profile import UserProfile
from coach.reasoning.coach.sections.base import ContextSection

# Standard distances in meters mapped to label and PB attribute name
_DISTANCE_TO_PB: list[tuple[float, str, str]] = [
    (1_000.0, '1K', 'PB_1K'),
    (5_000.0, '5K', 'PB_5K'),
    (10_000.0, '10K', 'PB_10K'),
    (15_000.0, '15K', 'PB_15K'),
    (21_097.5, 'Half Marathon', 'PB_HALF_MARATHON'),
    (42_195.0, 'Marathon', 'PB_MARATHON'),
]


def _parse_pace_to_seconds(pace_str: str) -> int:
    """Parse 'MM:SS/km' format to total seconds per km."""
    # Strip '/km' suffix
    time_part = pace_str.split('/')[0]
    parts = time_part.split(':')
    minutes = int(parts[0])
    seconds = int(parts[1])
    return minutes * 60 + seconds


def _find_matching_pb(
    goal_distance_meters: float,
    pb_summary: RunningPersonalBestsSummary,
) -> tuple[Optional[RunningPersonalBest], str]:
    """Return the matching PB and distance label for a goal distance, using ±5% proximity."""
    for standard_meters, label, attr_name in _DISTANCE_TO_PB:
        if abs(goal_distance_meters - standard_meters) / standard_meters <= 0.05:
            pb = getattr(pb_summary, attr_name)
            return pb, label
    return None, f'{goal_distance_meters:.0f}m'


class GoalStateSection(ContextSection):
    def __init__(self, profile: UserProfile, pb_summary: RunningPersonalBestsSummary) -> None:
        self._profile = profile
        self._pb_summary = pb_summary

    @property
    def header(self) -> str:
        return 'Goal fitness assessment:'

    def render(self) -> Optional[str]:
        goals = self._profile.goals or ()
        distance_goals = [g for g in goals if isinstance(g, DistanceActivityTrainingGoal)]

        if not distance_goals:
            return None

        lines: list[str] = []
        for goal in distance_goals:
            pb, distance_label = _find_matching_pb(goal.goal_distance_meters, self._pb_summary)

            if pb is not None:
                goal_seconds = _parse_pace_to_seconds(goal.goal_pace)
                pb_seconds = _parse_pace_to_seconds(pb.pace_str)
                gap = abs(pb_seconds - goal_seconds)
                direction = 'behind' if pb_seconds > goal_seconds else 'ahead of'
                lines.append(
                    f'{goal.name}: goal {goal.goal_pace} | current best {pb.pace_str} | {gap} sec/km {direction} target',
                )
            else:
                lines.append(f'{goal.name}: goal {goal.goal_pace} | no PB at {distance_label} recorded')

        return '\n'.join(lines)
