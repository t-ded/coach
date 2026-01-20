from abc import ABC
from abc import abstractmethod
from typing import Optional

from coach.domain.models import CoachResponse
from coach.domain.models import TrainingState


class CoachReasoner(ABC):
    @abstractmethod
    def reason(self, *, training_state: TrainingState, user_prompt: Optional[str] = None) -> CoachResponse:
        ...


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...
