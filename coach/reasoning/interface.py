from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Optional

from coach.domain.models import CoachResponse
from coach.domain.models import TrainingState


class ReasoningMode(Enum):
    ANALYSIS = 'analysis'
    CHAT = 'chat'


class CoachReasoner(ABC):
    @abstractmethod
    def analyze(self, *, training_state: TrainingState, user_prompt: Optional[str] = None) -> CoachResponse:
        ...

    @abstractmethod
    def chat(self, *, training_state: TrainingState, user_prompt: str, chat_history: Optional[str] = None) -> str:
        ...


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...
