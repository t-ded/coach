from datetime import UTC
from datetime import date
from datetime import datetime

from coach.builders.training_phase import detect_training_phase
from coach.domain.activity import SportType
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.training_analytics import TrainingMacroPhase


def _make_goal(
    name: str = 'Test Goal',
    goal_date: date | str = date(2025, 6, 1),
    priority: Priority = Priority.MEDIUM,
) -> TrainingGoal:
    return TrainingGoal(
        name=name,
        sport_type=SportType.RUN,
        goal_date=goal_date,
        priority=priority,
    )


class TestDetectTrainingPhaseNoGoals:
    def test_no_goals_returns_open(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        result = detect_training_phase((), generated_at)
        assert result.phase == TrainingMacroPhase.OPEN
        assert result.weeks_to_goal is None
        assert result.goal_name is None

    def test_string_goal_date_returns_open(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date='N/A')
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.OPEN

    def test_past_goal_date_returns_open(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        # Yesterday
        goal = _make_goal(goal_date=date(2025, 3, 16))
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.OPEN


class TestDetectTrainingPhaseThresholds:
    def test_3_days_out_is_race_week(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 3, 20))  # 3 days
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.RACE_WEEK
        assert result.weeks_to_goal == 0

    def test_7_days_out_is_race_week(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 3, 24))  # exactly 7 days
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.RACE_WEEK

    def test_14_days_out_is_taper(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 3, 31))  # 14 days
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.TAPER
        assert result.weeks_to_goal == 2

    def test_6_weeks_out_is_peak(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 4, 28))  # 42 days = 6 weeks
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.PEAK
        assert result.weeks_to_goal == 6

    def test_12_weeks_out_is_build(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 6, 9))  # 84 days = 12 weeks
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.BUILD
        assert result.weeks_to_goal == 12

    def test_20_weeks_out_is_base(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 8, 4))  # 140 days = 20 weeks
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.BASE
        assert result.weeks_to_goal == 20

    def test_goal_today_is_race_week(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(goal_date=date(2025, 3, 17))  # 0 days
        result = detect_training_phase((goal,), generated_at)
        assert result.phase == TrainingMacroPhase.RACE_WEEK


class TestDetectTrainingPhasePriorityAndProximity:
    def test_highest_priority_wins(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        low_goal = _make_goal(name='Low goal', goal_date=date(2025, 3, 24), priority=Priority.LOW)  # race week
        high_goal = _make_goal(name='High goal', goal_date=date(2025, 6, 9), priority=Priority.VERY_HIGH)  # build
        result = detect_training_phase((low_goal, high_goal), generated_at)
        assert result.phase == TrainingMacroPhase.BUILD
        assert result.goal_name == 'High goal'

    def test_equal_priority_nearest_wins(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        far_goal = _make_goal(name='Far goal', goal_date=date(2025, 6, 9), priority=Priority.HIGH)  # build
        near_goal = _make_goal(name='Near goal', goal_date=date(2025, 3, 31), priority=Priority.HIGH)  # taper
        result = detect_training_phase((far_goal, near_goal), generated_at)
        assert result.phase == TrainingMacroPhase.TAPER
        assert result.goal_name == 'Near goal'

    def test_goal_name_returned(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        goal = _make_goal(name='Sub-45 10K', goal_date=date(2025, 3, 31))
        result = detect_training_phase((goal,), generated_at)
        assert result.goal_name == 'Sub-45 10K'
