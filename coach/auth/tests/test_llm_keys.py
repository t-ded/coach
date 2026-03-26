from unittest.mock import MagicMock

from coach.auth.llm_keys import FakeLLMKeyRepository
from coach.auth.llm_keys import SupabaseLLMKeyRepository
from coach.reasoning.providers import LLMProvider

_USER_ID = 'user-123'
_GOOGLE = LLMProvider.GOOGLE
_OPENAI = LLMProvider.OPENAI
_GOOGLE_KEY = 'google-api-key'
_OPENAI_KEY = 'openai-api-key'


class TestSupabaseLLMKeyRepository:
    def setup_method(self) -> None:
        self.client = MagicMock()
        self.repo = SupabaseLLMKeyRepository(self.client)

    def test_get_key_returns_none_when_no_key_stored(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = []
        result = self.repo.get_key(_USER_ID, _GOOGLE)
        assert result is None

    def test_get_key_returns_key_when_row_exists(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = [{'api_key': _GOOGLE_KEY}]
        result = self.repo.get_key(_USER_ID, _GOOGLE)
        assert result == _GOOGLE_KEY

    def test_get_key_calls_rpc_with_correct_arguments(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = [{'api_key': _GOOGLE_KEY}]
        self.repo.get_key(_USER_ID, _GOOGLE)
        self.client.rpc.assert_called_once_with('get_ai_key', {'p_user_id': _USER_ID, 'p_provider': _GOOGLE})

    def test_save_key_calls_upsert_rpc_with_correct_arguments(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        self.client.rpc.assert_called_once_with(
            'upsert_ai_key',
            {'p_user_id': _USER_ID, 'p_provider': _GOOGLE, 'p_api_key': _GOOGLE_KEY},
        )

    def test_delete_key_calls_delete_rpc_with_correct_arguments(self) -> None:
        self.repo.delete_key(_USER_ID, _GOOGLE)
        self.client.rpc.assert_called_once_with('delete_ai_key', {'p_user_id': _USER_ID, 'p_provider': _GOOGLE})

    def test_list_providers_returns_empty_when_no_keys_stored(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = []
        result = self.repo.list_providers(_USER_ID)
        assert result == []

    def test_list_providers_returns_providers_for_stored_keys(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = [{'provider': 'google'}, {'provider': 'openai'}]
        result = self.repo.list_providers(_USER_ID)
        assert result == [_GOOGLE, _OPENAI]


class TestFakeLLMKeyRepository:
    def setup_method(self) -> None:
        self.repo = FakeLLMKeyRepository()

    def test_get_key_returns_none_when_no_key_stored(self) -> None:
        assert self.repo.get_key(_USER_ID, _GOOGLE) is None

    def test_get_key_returns_key_after_save(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        assert self.repo.get_key(_USER_ID, _GOOGLE) == _GOOGLE_KEY

    def test_save_key_replaces_existing_key(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        self.repo.save_key(_USER_ID, _GOOGLE, 'new-key')
        assert self.repo.get_key(_USER_ID, _GOOGLE) == 'new-key'

    def test_delete_key_removes_key(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        self.repo.delete_key(_USER_ID, _GOOGLE)
        assert self.repo.get_key(_USER_ID, _GOOGLE) is None

    def test_delete_key_is_noop_when_key_not_present(self) -> None:
        self.repo.delete_key(_USER_ID, _GOOGLE)  # should not raise

    def test_list_providers_returns_empty_when_no_keys_stored(self) -> None:
        assert self.repo.list_providers(_USER_ID) == []

    def test_list_providers_returns_providers_for_stored_keys(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        self.repo.save_key(_USER_ID, _OPENAI, _OPENAI_KEY)
        assert set(self.repo.list_providers(_USER_ID)) == {_GOOGLE, _OPENAI}

    def test_list_providers_isolates_by_user(self) -> None:
        self.repo.save_key(_USER_ID, _GOOGLE, _GOOGLE_KEY)
        self.repo.save_key('other-user', _OPENAI, _OPENAI_KEY)
        assert self.repo.list_providers(_USER_ID) == [_GOOGLE]
