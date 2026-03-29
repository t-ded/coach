from datetime import UTC
from datetime import datetime
from datetime import timedelta

from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.reasoning.coach.sections.profile import ProfileSection
from coach.reasoning.coach.sections.profile import render_training_goal


class TestProfileSection:
    def test_render_all_unset(self) -> None:
        section = ProfileSection(UserProfile())
        result = section.render()
        assert result is not None
        assert result.count('(not set)') == 4
        assert '--- Chat preferences ---' not in result

    def test_render_with_fields(self) -> None:
        profile = UserProfile(chat_preferences='Be concise.', training_preferences='Variety is key.')
        section = ProfileSection(profile)
        result = section.render()
        assert result is not None
        assert '--- Training preferences ---\nVariety is key.' in result
        assert '--- Personal information ---\n(not set)' in result
        assert '--- Chat preferences ---' not in result

    def test_render_with_goals(self) -> None:
        goal = TrainingGoal(name='Sub-20 5K', sport_type=SportType.RUN, goal_date='N/A', priority=Priority.HIGH)
        profile = UserProfile(goals=(goal,))
        section = ProfileSection(profile)
        result = section.render()
        assert result is not None
        assert 'Sub-20 5K' in result
        assert '(not set)' not in result.split('--- Goals ---')[1]


class TestRenderTrainingGoal:
    def test_distance_activity_goal(self) -> None:
        today = datetime.now(tz=UTC).date()
        goal_date = today + timedelta(days=10)

        training_goal = DistanceActivityTrainingGoal(
            name='Half-marathon at 1:45:00',
            sport_type=SportType.RUN,
            goal_date=goal_date,
            goal_distance_meters=21_097.5,
            goal_duration_seconds=6_300,
            goal_pace='5:00/km',
            notes='Would like to try for the PB before the race so that I go into the race knowing I can make it',
        )

        result = render_training_goal(training_goal)
        expected = f"""\
- Half-marathon at 1:45:00
    - Sport: Run
    - Goal date: {goal_date} (in 1 week and 3 days)
    - Distance: 21.0975 km
    - Total duration: 01:45:00
    - Pace: 5:00/km
    - Notes: Would like to try for the PB before the race so that I go into the race knowing I can make it
    - Priority: MEDIUM (Options were: ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'])"""

        assert result == expected

    def test_weight_training_goal(self) -> None:
        training_goal = TrainingGoal(
            name='Bench 120 kg',
            sport_type=SportType.STRENGTH,
            goal_date='N/A',
        )

        result = render_training_goal(training_goal)
        expected = """\
- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
    - Priority: MEDIUM (Options were: ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'])"""

        assert result == expected
