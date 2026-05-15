import pytest

from coach.reasoning.clients import AnthropicLLMClient
from coach.reasoning.clients import GoogleAILLMClient
from coach.reasoning.clients import LLMClient
from coach.reasoning.clients import OpenAILLMClient
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client


class TestCreateLLMClient:
    def test_google_uses_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('GOOGLE_AI_API_KEY', 'env-key')
        result = create_llm_client(provider=LLMProvider.GOOGLE)
        assert isinstance(result, GoogleAILLMClient)

    def test_google_uses_explicit_api_key(self) -> None:
        result = create_llm_client(provider=LLMProvider.GOOGLE, api_key='explicit-key')
        assert isinstance(result, GoogleAILLMClient)

    def test_google_raises_when_no_key_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('GOOGLE_AI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='No API key'):
            create_llm_client(provider=LLMProvider.GOOGLE)

    def test_openai_uses_explicit_api_key(self) -> None:
        result = create_llm_client(provider=LLMProvider.OPENAI, api_key='explicit-key')
        assert isinstance(result, OpenAILLMClient)

    def test_openai_uses_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('OPENAI_API_KEY', 'env-key')
        result = create_llm_client(provider=LLMProvider.OPENAI)
        assert isinstance(result, OpenAILLMClient)

    def test_openai_raises_when_no_key_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='No API key'):
            create_llm_client(provider=LLMProvider.OPENAI)

    def test_anthropic_uses_explicit_api_key(self) -> None:
        result = create_llm_client(provider=LLMProvider.ANTHROPIC, api_key='explicit-key')
        assert isinstance(result, AnthropicLLMClient)

    def test_anthropic_uses_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'env-key')
        result = create_llm_client(provider=LLMProvider.ANTHROPIC)
        assert isinstance(result, AnthropicLLMClient)

    def test_anthropic_raises_when_no_key_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        with pytest.raises(ValueError, match='No API key'):
            create_llm_client(provider=LLMProvider.ANTHROPIC)

    def test_returns_llm_client_interface(self) -> None:
        result = create_llm_client(provider=LLMProvider.ANTHROPIC, api_key='any-key')
        assert isinstance(result, LLMClient)
