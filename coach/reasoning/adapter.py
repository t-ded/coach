from typing import Optional

from coach.domain.models import CoachResponse
from coach.domain.models import TrainingState
from coach.reasoning.context import render_training_state_for_reasoning
from coach.reasoning.interface import CoachReasoner
from coach.reasoning.interface import LLMClient
from coach.reasoning.parsing import parse_coach_response
from coach.reasoning.prompts import build_coach_prompt


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

        raw_response = self._llm_client.complete(prompt)
        return parse_coach_response(raw_response)
