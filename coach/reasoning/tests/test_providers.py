import pytest

from coach.reasoning.clients import LLMClient
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client
from coach.reasoning.providers import resolve_provider_and_key


class TestResolveProviderAndKey:
    def test_user_google_key_takes_priority_over_operator(self) -> None:
        result = resolve_provider_and_key({'GOOGLE_AI_API_KEY': 'user-key'}, {'GOOGLE_AI_API_KEY': 'op-key'})
        assert result == (LLMProvider.GOOGLE, 'user-key')

    def test_user_openai_key_returns_openai_provider(self) -> None:
        result = resolve_provider_and_key({'OPENAI_API_KEY': 'user-key'}, {})
        assert result == (LLMProvider.OPENAI, 'user-key')

    def test_google_wins_over_openai_in_user_env(self) -> None:
        result = resolve_provider_and_key({'GOOGLE_AI_API_KEY': 'g', 'OPENAI_API_KEY': 'o'}, {})
        assert result == (LLMProvider.GOOGLE, 'g')

    def test_falls_back_to_operator_google_key(self) -> None:
        result = resolve_provider_and_key({}, {'GOOGLE_AI_API_KEY': 'op-key'})
        assert result == (LLMProvider.GOOGLE, 'op-key')

    def test_empty_user_key_falls_through_to_operator(self) -> None:
        result = resolve_provider_and_key({'GOOGLE_AI_API_KEY': ''}, {'GOOGLE_AI_API_KEY': 'op-key'})
        assert result == (LLMProvider.GOOGLE, 'op-key')

    def test_raises_when_no_keys_available(self) -> None:
        with pytest.raises(ValueError, match='No LLM API key'):
            resolve_provider_and_key({}, {})


class TestCreateLLMClient:
    def test_uses_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('GOOGLE_AI_API_KEY', 'env-key')
        result = create_llm_client(provider=LLMProvider.GOOGLE)
        assert isinstance(result, LLMClient)

    def test_uses_explicit_api_key(self) -> None:
        result = create_llm_client(provider=LLMProvider.GOOGLE, api_key='explicit-key')
        assert isinstance(result, LLMClient)

    def test_raises_when_no_key_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('GOOGLE_AI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='No API key'):
            create_llm_client(provider=LLMProvider.GOOGLE)
