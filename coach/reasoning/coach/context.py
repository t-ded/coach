from typing import Optional

from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.profile import UserProfile
from coach.domain.training_summaries import RecentTrainingHistory
from coach.reasoning.coach.sections import ContextSection
from coach.reasoning.coach.sections import PersonalBestsSection
from coach.reasoning.coach.sections import ProfileSection
from coach.reasoning.coach.sections import TrainingHistorySection
from coach.reasoning.coach.sections.utils import combine_sections


def build_coach_context(
    *,
    profile: Optional[UserProfile],
    recent_training_history: RecentTrainingHistory,
    pb_summary: RunningPersonalBestsSummary,
) -> Optional[str]:
    sections: list[ContextSection] = []
    if profile:
        sections.append(ProfileSection(profile))
    sections.append(TrainingHistorySection(recent_training_history))
    sections.append(PersonalBestsSection(pb_summary))

    rendered_pairs = [(s.header, s.render()) for s in sections]
    parts = combine_sections(rendered_pairs)
    return '\n'.join(parts) or None
