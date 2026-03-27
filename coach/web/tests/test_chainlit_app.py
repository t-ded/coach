from coach.auth.llm_keys import FakeLLMKeyRepository
from coach.reasoning.providers import LLMProvider
from coach.web.api_key_flow import _PROVIDER_DISPLAY_NAMES
from coach.web.chainlit_app import _resolve_llm_key

_USER_ID = 'user-123'
_GOOGLE = LLMProvider.GOOGLE
_OPENAI = LLMProvider.OPENAI


class TestResolveLLMKey:
    def setup_method(self) -> None:
        self._repo = FakeLLMKeyRepository()

    def test_returns_preferred_key_and_no_notice(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        key, provider, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'g-key'
        assert provider == _GOOGLE
        assert notice is None

    def test_falls_back_to_other_provider_when_preferred_missing(self) -> None:
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        key, provider, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'o-key'
        assert provider == _OPENAI

    def test_fallback_notice_names_both_providers_parametrically(self) -> None:
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        _, _, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert notice is not None
        assert _PROVIDER_DISPLAY_NAMES[_OPENAI] in notice
        assert _PROVIDER_DISPLAY_NAMES[_GOOGLE] in notice

    def test_returns_none_key_when_no_keys_stored(self) -> None:
        key, provider, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key is None
        assert provider == _GOOGLE
        assert notice is None

    def test_preferred_provider_key_wins_over_fallback(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        key, provider, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'g-key'
        assert provider == _GOOGLE
        assert notice is None

    def test_no_notice_when_preferred_key_is_present(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        _, _, notice = _resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert notice is None
