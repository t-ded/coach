import time
from abc import ABC
from abc import abstractmethod
from typing import Optional

from google import genai
from google.genai import types
from openai import OpenAI

from coach.reasoning.interface import LLMClient


class BaseLLMClient(LLMClient, ABC):
    def __init__(self, *, max_retries: int = 3) -> None:
        self._max_retries = max_retries

    def complete(self, prompt: str) -> str:
        last_error: Optional[Exception] = None

        for _ in range(self._max_retries):
            try:
                return self._call_api(prompt)
            except Exception as exc:
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                last_error = exc
                time.sleep(1)

        raise RuntimeError('LLM request failed') from last_error

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """Provider-specific API call implementation."""
        ...


class GoogleAILLMClient(BaseLLMClient):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = 'gemini-2.0-flash-exp',
        max_retries: int = 3,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(max_retries=max_retries)
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._generation_config = types.GenerateContentConfig(max_output_tokens=max_output_tokens)

    def _call_api(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._generation_config,
        )
        if response.text is None:
            raise ValueError('Empty response from Google AI API')
        return response.text


class OpenAILLMClient(BaseLLMClient):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = 'gpt-5-nano',
        max_retries: int = 3,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(max_retries=max_retries)
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._client = OpenAI(api_key=api_key, max_retries=self._max_retries)

    def _call_api(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
            max_output_tokens=self._max_output_tokens,
        )
        return response.output_text
