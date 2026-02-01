from pathlib import Path
from typing import Optional

from coach.domain.training_summaries import RecentTrainingHistory
from coach.reasoning.context import render_recent_training_history
from coach.reasoning.context import render_system_prompt
from coach.reasoning.interface import CoachReasoner
from coach.reasoning.interface import LLMClient
from coach.reasoning.prompts import build_coach_prompt
from coach.utils import parse_file


class LLMCoachReasoner(CoachReasoner):
    def __init__(self, llm_client: LLMClient, user_system_prompt_path: Path = Path('coach/config/coach.md')) -> None:
        self._llm_client = llm_client
        self._rendered_system_prompt = render_system_prompt(parse_file(user_system_prompt_path))

    def chat(self, *, recent_training_history: RecentTrainingHistory, user_prompt: str, chat_history: Optional[str] = None) -> str:
        rendered_history = render_recent_training_history(recent_training_history)
        prompt = build_coach_prompt(rendered_recent_training_history=rendered_history, user_prompt=user_prompt, rendered_system_prompt=self._rendered_system_prompt, chat_history=chat_history)
        return self._llm_client.complete(prompt)
