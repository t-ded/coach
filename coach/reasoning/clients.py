import time
from typing import Optional

from openai import OpenAI

from coach.reasoning.interface import LLMClient


class OpenAILLMClient(LLMClient):
    def __init__(
        self,
        *,
        client: Optional[OpenAI] = None,
        model: str = 'gpt-5-nano',
        max_retries: int = 3,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        self._client = client or OpenAI()
        self._model = model
        self._max_retries = max_retries
        self._max_output_tokens = max_output_tokens

    def complete(self, prompt: str) -> str:
        last_error: Optional[Exception] = None

        for _ in range(self._max_retries):
            try:
                response = self._client.responses.create(
                    model=self._model,
                    input=prompt,
                    max_output_tokens=self._max_output_tokens,
                )
                return response.output_text
            except Exception as exc:
                last_error = exc
                time.sleep(1)

        raise RuntimeError('LLM request failed') from last_error
