from coach.auth.llm_keys import FakeLLMKeyRepository
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import display_provider
from coach.web.api_key_flow import _build_management_actions
from coach.web.api_key_flow import _build_management_text
from coach.web.api_key_flow import _help_text
from coach.web.api_key_flow import resolve_llm_key

_GOOGLE = LLMProvider.GOOGLE
_OPENAI = LLMProvider.OPENAI
_USER_ID = 'user-123'


class TestBuildManagementText:
    def test_no_keys_stored(self) -> None:
        text = _build_management_text(_GOOGLE, [])
        assert 'No API keys are stored' in text

    def test_shows_preferred_provider(self) -> None:
        text = _build_management_text(_GOOGLE, [_GOOGLE])
        assert 'Google AI Studio' in text
        assert 'preferred' in text

    def test_marks_preferred_provider_in_list(self) -> None:
        text = _build_management_text(_GOOGLE, [_GOOGLE, _OPENAI])
        google_pos = text.index('Google AI Studio')
        preferred_pos = text.index('preferred')
        # preferred marker should appear near Google AI Studio, not OpenAI
        openai_pos = text.index('OpenAI')
        assert abs(google_pos - preferred_pos) < abs(openai_pos - preferred_pos)

    def test_does_not_mark_non_preferred_provider(self) -> None:
        text = _build_management_text(_GOOGLE, [_GOOGLE, _OPENAI])
        # OpenAI line should not have the preferred marker
        openai_line = next(line for line in text.splitlines() if 'OpenAI' in line)
        assert 'preferred' not in openai_line

    def test_lists_all_stored_providers(self) -> None:
        text = _build_management_text(_GOOGLE, [_GOOGLE, _OPENAI])
        assert 'Google AI Studio' in text
        assert 'OpenAI' in text


class TestBuildManagementActions:
    def _action_names(self, preferred: LLMProvider, stored: list[LLMProvider]) -> list[str]:
        return [a.name for a in _build_management_actions(preferred, stored)]

    def _action_labels(self, preferred: LLMProvider, stored: list[LLMProvider]) -> list[str]:
        return [a.label for a in _build_management_actions(preferred, stored)]

    def test_add_button_for_unstored_provider(self) -> None:
        names = self._action_names(_GOOGLE, [_GOOGLE])
        assert 'add_provider_key' in names

    def test_no_add_button_when_all_providers_stored(self) -> None:
        names = self._action_names(_GOOGLE, [_GOOGLE, _OPENAI])
        assert 'add_provider_key' not in names

    def test_remove_button_for_each_stored_provider(self) -> None:
        actions = _build_management_actions(_GOOGLE, [_GOOGLE, _OPENAI])
        remove_actions = [a for a in actions if a.name == 'remove_provider_key']
        assert len(remove_actions) == 2

    def test_set_preferred_button_only_for_non_preferred_stored(self) -> None:
        actions = _build_management_actions(_GOOGLE, [_GOOGLE, _OPENAI])
        set_pref = [a for a in actions if a.name == 'set_preferred_provider']
        assert len(set_pref) == 1
        assert set_pref[0].payload['provider'] == 'openai'

    def test_no_set_preferred_button_when_only_one_provider(self) -> None:
        names = self._action_names(_GOOGLE, [_GOOGLE])
        assert 'set_preferred_provider' not in names

    def test_remove_button_payload_contains_provider(self) -> None:
        actions = _build_management_actions(_GOOGLE, [_GOOGLE])
        remove = next(a for a in actions if a.name == 'remove_provider_key')
        assert remove.payload['provider'] == 'google'

    def test_add_button_payload_contains_provider(self) -> None:
        actions = _build_management_actions(_GOOGLE, [_GOOGLE])
        add = next(a for a in actions if a.name == 'add_provider_key')
        assert add.payload['provider'] == 'openai'

    def test_no_actions_when_no_keys_stored(self) -> None:
        # With no stored keys, we show add buttons for all providers plus cancel
        names = self._action_names(_GOOGLE, [])
        assert all(n in ('add_provider_key', 'cancel_provider_management') for n in names)
        assert names.count('add_provider_key') == len(list(LLMProvider))

    def test_cancel_button_always_present(self) -> None:
        assert 'cancel_provider_management' in self._action_names(_GOOGLE, [])
        assert 'cancel_provider_management' in self._action_names(_GOOGLE, [_GOOGLE])
        assert 'cancel_provider_management' in self._action_names(_GOOGLE, [_GOOGLE, _OPENAI])


class TestHelpText:
    def test_contains_google_setup_steps(self) -> None:
        text = _help_text()
        assert 'aistudio.google.com/apikey' in text

    def test_contains_openai_setup_steps(self) -> None:
        text = _help_text()
        assert 'platform.openai.com/api-keys' in text

    def test_contains_readme_link(self) -> None:
        text = _help_text()
        assert 'README' in text

    def test_contains_manage_ai_provider_instruction(self) -> None:
        text = _help_text()
        assert 'Manage AI Provider' in text


class TestResolveLLMKey:
    def setup_method(self) -> None:
        self._repo = FakeLLMKeyRepository()

    def test_returns_preferred_key_and_no_notice(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        key, provider, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'g-key'
        assert provider == _GOOGLE
        assert notice is None

    def test_falls_back_to_other_provider_when_preferred_missing(self) -> None:
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        key, provider, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'o-key'
        assert provider == _OPENAI

    def test_fallback_notice_names_both_providers(self) -> None:
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        _, _, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert notice is not None
        assert display_provider(_OPENAI) in notice
        assert display_provider(_GOOGLE) in notice

    def test_returns_none_key_when_no_keys_stored(self) -> None:
        key, provider, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key is None
        assert provider == _GOOGLE
        assert notice is None

    def test_preferred_provider_key_wins_over_fallback(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        self._repo.save_key(_USER_ID, _OPENAI, 'o-key')
        key, provider, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert key == 'g-key'
        assert provider == _GOOGLE
        assert notice is None

    def test_no_notice_when_preferred_key_is_present(self) -> None:
        self._repo.save_key(_USER_ID, _GOOGLE, 'g-key')
        _, _, notice = resolve_llm_key(self._repo, _USER_ID, _GOOGLE)
        assert notice is None
