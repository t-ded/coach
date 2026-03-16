from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from coach.domain.goals import TrainingGoal


@dataclass
class UserProfile:
    chat_preferences: Optional[str] = field(default=None)
    training_preferences: Optional[str] = field(default=None)
    personal_information: Optional[str] = field(default=None)
    constraints: Optional[str] = field(default=None)
    goals: list[TrainingGoal] = field(default_factory=list)

    # TODO: Persist this to DB after the refactor
    @classmethod
    def mock(cls) -> UserProfile:
        return cls(
            chat_preferences='Be a helpful assistant',
            training_preferences='',
            personal_information='',
            constraints='',
            goals=[],
        )
