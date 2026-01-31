from datetime import date

from coach.builders.training_goal import build_training_goal
from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import TrainingGoal


class TestBuildTrainingGoal:
    def test_minimal_training_goal(self) -> None:
        goal_description = """
- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
"""

        training_goal = build_training_goal(goal_description)
        expected_training_goal = TrainingGoal(
            sport_type=SportType.STRENGTH,
            name='Bench 120 kg',
            goal_date='N/A',
        )

        assert training_goal == expected_training_goal

    def test_distance_based_training_goal_with_distance_and_duration(self) -> None:
        goal_description = """
- Sub20 5K
    - Sport: Run
    - Goal date: 2026-06-30
    - Distance: 5 km
    - Total duration: 00:20:00
    - Notes: Would like to try for the PB before the race so that I go into the race knowing I can make it

        """

        training_goal = build_training_goal(goal_description)
        expected_training_goal = DistanceActivityTrainingGoal(
            sport_type=SportType.RUN,
            name='Sub20 5K',
            goal_date=date(2026, 6, 30),
            notes='Would like to try for the PB before the race so that I go into the race knowing I can make it',
            goal_distance_meters=5_000,
            goal_duration_seconds=1_200,
            goal_pace='4:00/km',
        )

        assert training_goal == expected_training_goal
