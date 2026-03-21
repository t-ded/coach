from pathlib import Path

import pytest

from coach.config.credentials import CredentialsStore
from coach.reasoning.clients import LLMClient
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client


class TestCreateLLMClientGoogleKeyResolution:
    def test_uses_env_var_when_set(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv('GOOGLE_AI_API_KEY', 'env-key')
        empty_store = CredentialsStore(config_dir=tmp_path)
        monkeypatch.setattr('coach.reasoning.providers.CredentialsStore', lambda: empty_store)

        result = create_llm_client(provider=LLMProvider.GOOGLE)

        assert isinstance(result, LLMClient)

    def test_falls_back_to_credentials_store_when_no_env_var(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.delenv('GOOGLE_AI_API_KEY', raising=False)
        store = CredentialsStore(config_dir=tmp_path)
        store.store_google_api_key('stored-key')
        monkeypatch.setattr('coach.reasoning.providers.CredentialsStore', lambda: store)

        result = create_llm_client(provider=LLMProvider.GOOGLE)

        assert isinstance(result, LLMClient)

    def test_raises_when_neither_env_var_nor_credentials_store(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.delenv('GOOGLE_AI_API_KEY', raising=False)
        empty_store = CredentialsStore(config_dir=tmp_path)
        monkeypatch.setattr('coach.reasoning.providers.CredentialsStore', lambda: empty_store)

        with pytest.raises(ValueError, match='No Google credentials found'):
            create_llm_client(provider=LLMProvider.GOOGLE)
