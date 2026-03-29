from datetime import datetime
from typing import Optional

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.reasoning.coach.sections import ContextSection
from coach.reasoning.coach.sections import PersonalBestsSection
from coach.reasoning.coach.sections import ProfileSection
from coach.reasoning.coach.sections import TrainingHistorySection
from coach.reasoning.coach.sections.utils import combine_sections


def build_coach_context(
    *,
    profile: Optional[UserProfile],
    activities: list[Activity],
    num_history_weeks: int,
    generated_at: datetime,
) -> Optional[str]:
    pb_summary = build_running_personal_bests_summary(activities=activities)
    recent_training_history = build_recent_training_history(
        activities=activities,
        generated_at=generated_at,
        num_history_weeks=num_history_weeks,
    )

    sections: list[ContextSection] = []
    if profile:
        sections.append(ProfileSection(profile))
    sections.append(TrainingHistorySection(recent_training_history))
    sections.append(PersonalBestsSection(pb_summary))

    rendered_pairs = [(s.header, s.render()) for s in sections]
    parts = combine_sections(rendered_pairs)
    return '\n'.join(parts) or None
