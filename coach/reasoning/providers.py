import os
from enum import StrEnum
from typing import Optional

from coach.reasoning.clients import GoogleAILLMClient
from coach.reasoning.clients import LLMClient
from coach.reasoning.clients import OpenAILLMClient

_ENV_KEYS: dict[str, str] = {
    'google': 'GOOGLE_AI_API_KEY',
    'openai': 'OPENAI_API_KEY',
}


class LLMProvider(StrEnum):
    GOOGLE = 'google'
    OPENAI = 'openai'


_PROVIDER_DISPLAY_NAMES: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: 'Google AI Studio',
    LLMProvider.OPENAI: 'OpenAI',
}


def display_provider(provider: LLMProvider) -> str:
    return _PROVIDER_DISPLAY_NAMES.get(provider, provider.value.title())


def create_llm_client(
    provider: LLMProvider = LLMProvider.GOOGLE,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
) -> LLMClient:
    key = api_key or os.environ.get(_ENV_KEYS[provider])
    if not key:
        msg = f'No API key found for {provider}. Set {_ENV_KEYS[provider]} env var.'
        raise ValueError(msg)

    if provider == LLMProvider.GOOGLE:
        return GoogleAILLMClient(api_key=key, model=model or 'gemini-2.5-flash', max_retries=max_retries)

    if provider == LLMProvider.OPENAI:
        return OpenAILLMClient(api_key=key, model=model or 'gpt-5.4-nano', max_retries=max_retries)

    raise ValueError(f'Unsupported provider: {provider}')
