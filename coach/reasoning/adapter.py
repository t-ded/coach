from typing import Optional

from coach.config.config import MAX_CORRECTION_RETRIES
from coach.domain.models import CoachResponse
from coach.domain.models import TrainingState
from coach.reasoning.context import render_training_state_for_reasoning
from coach.reasoning.interface import CoachReasoner
from coach.reasoning.interface import LLMClient
from coach.reasoning.parsing import CoachResponseParseError
from coach.reasoning.parsing import parse_coach_response
from coach.reasoning.prompts import build_coach_prompt
from coach.reasoning.prompts import generate_output_instructions


class LLMCoachReasoner(CoachReasoner):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def reason(
        self,
        *,
        training_state: TrainingState,
        user_prompt: Optional[str] = None,
    ) -> CoachResponse:
        rendered_state = render_training_state_for_reasoning(training_state)

        prompt = build_coach_prompt(
            rendered_training_state=rendered_state,
            user_prompt=user_prompt,
        )

        attempt = 0

        while True:
            raw_response = self._llm_client.complete(prompt)

            try:
                return parse_coach_response(raw_response)
            except CoachResponseParseError as exc:
                if attempt <= MAX_CORRECTION_RETRIES:
                    prompt = self._get_retry_prompt(exc, raw_response)
                else:
                    raise exc

            attempt += 1

    @staticmethod
    def _get_retry_prompt(exception: Exception, raw_response: str) -> str:
        return (
            f'The previous response was invalid because: {exception}\n'
            f'Please return the same content but correctly formatted according to the following structure:\n'
            f'{generate_output_instructions()}\n\n'
            f'Original response:\n{raw_response}'
        )
