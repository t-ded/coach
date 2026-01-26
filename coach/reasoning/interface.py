from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Optional

from coach.domain.chat import CoachResponse
from coach.domain.training_summaries import RecentTrainingHistory


class ReasoningMode(Enum):
    ANALYSIS = 'analysis'
    CHAT = 'chat'


class CoachReasoner(ABC):
    @abstractmethod
    def analyze(self, *, recent_training_history: RecentTrainingHistory, user_prompt: Optional[str] = None) -> CoachResponse:
        ...

    @abstractmethod
    def chat(self, *, recent_training_history: RecentTrainingHistory, user_prompt: str, chat_history: Optional[str] = None) -> str:
        ...


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...
