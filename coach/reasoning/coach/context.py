from typing import Optional

from coach.builders.training_phase import detect_training_phase
from coach.builders.training_trends import build_training_trends
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.profile import UserProfile
from coach.domain.training_summaries import RecentTrainingHistory
from coach.reasoning.coach.sections import ContextSection
from coach.reasoning.coach.sections import GoalStateSection
from coach.reasoning.coach.sections import PersonalBestsSection
from coach.reasoning.coach.sections import ProfileSection
from coach.reasoning.coach.sections import TrainingHistorySection
from coach.reasoning.coach.sections import TrainingPhaseSection
from coach.reasoning.coach.sections import TrainingTrendsSection
from coach.reasoning.coach.sections.utils import combine_sections


def build_coach_context(
    *,
    profile: Optional[UserProfile],
    recent_training_history: RecentTrainingHistory,
    pb_summary: RunningPersonalBestsSummary,
) -> Optional[str]:
    training_trends = build_training_trends(recent_training_history)
    training_phase = detect_training_phase(
        profile.goals if profile and profile.goals else (),
        recent_training_history.generated_at,
    )

    sections: list[ContextSection] = []
    sections.append(TrainingPhaseSection(training_phase))
    if profile:
        sections.append(ProfileSection(profile))
        sections.append(GoalStateSection(profile, pb_summary))
    sections.append(TrainingTrendsSection(training_trends))
    sections.append(TrainingHistorySection(recent_training_history))
    sections.append(PersonalBestsSection(pb_summary))

    rendered_pairs = [(s.header, s.render()) for s in sections]
    parts = combine_sections(rendered_pairs)
    if not parts:
        return None
    date_anchor = recent_training_history.generated_at.strftime("Today's date: %A, %B %d, %Y")
    return '\n'.join([date_anchor, *parts])
