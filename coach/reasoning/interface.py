from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

from coach.domain.models import TrainingState


@dataclass(frozen=True, kw_only=True, slots=True)
class CoachResponse:
    summary: str
    observations: list[str]
    recommendations: list[str]
    confidence_notes: Optional[str]


class CoachReasoner(ABC):
    @abstractmethod
    def reason(self, *, training_state: TrainingState, user_prompt: Optional[str] = None) -> CoachResponse:
        ...
