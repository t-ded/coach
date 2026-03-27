import pytest

from coach.reasoning.clients import LLMClient
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client


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
