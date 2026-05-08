from coach.domain.training_analytics import ActiveTrainingPhase
from coach.domain.training_analytics import TrainingMacroPhase
from coach.reasoning.coach.sections.training_phase import TrainingPhaseSection


def _make_phase(
    phase: TrainingMacroPhase,
    weeks_to_goal: int | None = None,
    goal_name: str | None = None,
) -> ActiveTrainingPhase:
    return ActiveTrainingPhase(phase=phase, weeks_to_goal=weeks_to_goal, goal_name=goal_name)


class TestTrainingPhaseSectionOpen:
    def test_open_phase_renders_correctly(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.OPEN))
        result = section.render()
        assert result == 'Open training — no active goal with a future date set.'


class TestTrainingPhaseSectionNonOpen:
    def test_taper_phase_renders_name_weeks_and_focus(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.TAPER, weeks_to_goal=2, goal_name='Sub-45 10K'))
        result = section.render()
        assert result is not None
        assert 'Phase: Taper (towards Sub-45 10K, 2 weeks to goal)' in result
        assert 'Focus: Reduce volume 20-30%' in result

    def test_base_phase_renders_focus(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.BASE, weeks_to_goal=20, goal_name='Marathon'))
        result = section.render()
        assert result is not None
        assert 'Phase: Base building' in result
        assert 'Focus: Build aerobic base' in result

    def test_build_phase_renders_focus(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.BUILD, weeks_to_goal=12, goal_name='10K race'))
        result = section.render()
        assert result is not None
        assert 'Phase: Build / specificity' in result
        assert 'Focus: Increase specificity' in result

    def test_peak_phase_renders_focus(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.PEAK, weeks_to_goal=5, goal_name='Half Marathon'))
        result = section.render()
        assert result is not None
        assert 'Phase: Peak' in result
        assert 'Focus: Race-specific intensity' in result

    def test_race_week_phase_renders_focus(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.RACE_WEEK, weeks_to_goal=0, goal_name='5K race'))
        result = section.render()
        assert result is not None
        assert 'Phase: Race week' in result
        assert 'Focus: Minimal volume' in result

    def test_singular_week_suffix(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.TAPER, weeks_to_goal=1, goal_name='10K'))
        result = section.render()
        assert result is not None
        assert '1 week to goal' in result

    def test_plural_weeks_suffix(self) -> None:
        section = TrainingPhaseSection(_make_phase(TrainingMacroPhase.BUILD, weeks_to_goal=8, goal_name='Marathon'))
        result = section.render()
        assert result is not None
        assert '8 weeks to goal' in result
