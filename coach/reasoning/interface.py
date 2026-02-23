from abc import ABC
from abc import abstractmethod
from typing import Optional

from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.training_summaries import RecentTrainingHistory


class CoachReasoner(ABC):
    @abstractmethod
    def chat(self, *, running_pbs: RunningPersonalBestsSummary, recent_training_history: RecentTrainingHistory, user_prompt: str, chat_history: Optional[str] = None) -> str:
        ...


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...
