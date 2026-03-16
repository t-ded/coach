from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from coach.domain.goals import TrainingGoal


@dataclass(frozen=True, kw_only=True, slots=True)
class UserProfile:
    chat_preferences: Optional[str] = field(default=None)
    training_preferences: Optional[str] = field(default=None)
    personal_information: Optional[str] = field(default=None)
    constraints: Optional[str] = field(default=None)
    goals: Optional[tuple[TrainingGoal, ...]] = field(default=None)

    # TODO: Remove once ProfileAssistant + persistence are wired up
    @classmethod
    def mock(cls) -> UserProfile:
        return cls(chat_preferences='Respond concisely. Avoid restating the question or summarizing what you are about to say.')
