from enum import StrEnum
from typing import Optional

from coach.auth.utils import no_credentials_found_message
from coach.config.credentials import CredentialsStore
from coach.reasoning.clients import GoogleAILLMClient
from coach.reasoning.clients import LLMClient
from coach.reasoning.clients import OpenAILLMClient


class LLMProvider(StrEnum):
    GOOGLE = 'google'
    OPENAI = 'openai'


def _get_api_key(provider: LLMProvider) -> str:
    store = CredentialsStore()

    if provider == LLMProvider.GOOGLE:
        api_key = store.get_google_api_key()
    elif provider == LLMProvider.OPENAI:
        api_key = store.get_openai_api_key()
    else:
        msg = f'Unsupported provider: {provider}'
        raise ValueError(msg)

    if not api_key:
        msg = no_credentials_found_message(provider.value)
        raise ValueError(msg)

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
            model=model or 'gemini-2.5-flash',
            max_retries=max_retries,
        )

    if provider == LLMProvider.OPENAI:
        return OpenAILLMClient(
            api_key=api_key,
            model=model or 'gpt-5-nano',
            max_retries=max_retries,
        )

    raise ValueError(f'Unsupported provider: {provider}')
