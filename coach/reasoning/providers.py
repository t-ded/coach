import os
from enum import StrEnum
from typing import Optional

from coach.reasoning.clients import GoogleAILLMClient
from coach.reasoning.clients import OpenAILLMClient
from coach.reasoning.interface import LLMClient


class LLMProvider(StrEnum):
    GOOGLE = 'google'
    OPENAI = 'openai'


API_KEY_NAMES_MAPPING = {
    LLMProvider.GOOGLE: 'GOOGLE_AI_API_KEY',
    LLMProvider.OPENAI: 'OPENAI_API_KEY',
}


def _get_api_key(provider: LLMProvider) -> str:
    if provider not in API_KEY_NAMES_MAPPING:
        raise ValueError(f'Unsupported provider: {provider}.')

    api_key_name = API_KEY_NAMES_MAPPING[provider]
    api_key = os.getenv(api_key_name)

    if not api_key:
        raise ValueError(f'{api_key_name} environment variable is required for {provider}')

    return api_key


def create_llm_client(
    provider: LLMProvider = LLMProvider.GOOGLE,
    model: Optional[str] = None,
    max_retries: int = 3,
) -> LLMClient:
    api_key = _get_api_key(provider)
    if provider == LLMProvider.GOOGLE:
        return GoogleAILLMClient(
            api_key=api_key,
            model=model or 'gemini-2.0-flash-exp',
            max_retries=max_retries,
        )

    if provider == LLMProvider.OPENAI:
        return OpenAILLMClient(
            api_key=api_key,
            model=model or 'gpt-5-nano',
            max_retries=max_retries,
        )

    raise ValueError(f'Unsupported provider: {provider}')
