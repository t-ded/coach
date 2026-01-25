from typing import Optional

from coach.config.config import MAX_CORRECTION_RETRIES
from coach.domain.models import CoachResponse
from coach.domain.models import RecentTrainingHistory
from coach.reasoning.context import render_recent_training_history
from coach.reasoning.interface import CoachReasoner
from coach.reasoning.interface import LLMClient
from coach.reasoning.parsing import CoachResponseParseError
from coach.reasoning.parsing import parse_coach_response
from coach.reasoning.prompts import INITIAL_OUTPUT_INSTRUCTIONS
from coach.reasoning.prompts import build_coach_prompt


class LLMCoachReasoner(CoachReasoner):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def analyze(self, *, recent_training_history: RecentTrainingHistory, user_prompt: Optional[str] = None) -> CoachResponse:
        rendered_history = render_recent_training_history(recent_training_history)
        prompt = build_coach_prompt(rendered_recent_training_history=rendered_history, user_prompt=user_prompt)
        return self._parse_analyze_response_with_retry(prompt)

    def chat(self, *, recent_training_history: RecentTrainingHistory, user_prompt: str, chat_history: Optional[str] = None) -> str:
        rendered_history = render_recent_training_history(recent_training_history)
        prompt = build_coach_prompt(rendered_recent_training_history=rendered_history, user_prompt=user_prompt, chat_history=chat_history)
        return self._llm_client.complete(prompt)

    def _parse_analyze_response_with_retry(self, prompt: str) -> CoachResponse:
        attempt = 0

        while True:
            raw_response = self._llm_client.complete(prompt)

            try:
                return parse_coach_response(raw_response)
            except CoachResponseParseError as exc:
                if attempt <= MAX_CORRECTION_RETRIES:
                    prompt = self._get_analyze_retry_prompt(exc, raw_response)
                else:
                    raise exc

            attempt += 1

    @staticmethod
    def _get_analyze_retry_prompt(exception: Exception, raw_response: str) -> str:
        return (
            f'The previous response was invalid because: {exception}\n'
            f'Please return the same content but correctly formatted according to the following structure:\n'
            f'{INITIAL_OUTPUT_INSTRUCTIONS}\n\n'
            f'Original response:\n{raw_response}'
        )
