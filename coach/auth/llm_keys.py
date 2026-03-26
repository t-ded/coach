from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Optional
from typing import cast

from supabase import Client

from coach.reasoning.providers import LLMProvider


class LLMKeyRepository(ABC):
    @abstractmethod
    def get_key(self, user_id: str, provider: LLMProvider) -> Optional[str]: ...

    @abstractmethod
    def save_key(self, user_id: str, provider: LLMProvider, api_key: str) -> None: ...

    @abstractmethod
    def delete_key(self, user_id: str, provider: LLMProvider) -> None: ...

    @abstractmethod
    def list_providers(self, user_id: str) -> list[LLMProvider]: ...


class SupabaseLLMKeyRepository(LLMKeyRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_key(self, user_id: str, provider: LLMProvider) -> Optional[str]:
        response = self._client.rpc('get_ai_key', {'p_user_id': user_id, 'p_provider': provider}).execute()
        rows = cast(list[dict[str, Any]], response.data)
        if not rows:
            return None
        return cast(str, rows[0]['api_key'])

    def save_key(self, user_id: str, provider: LLMProvider, api_key: str) -> None:
        self._client.rpc(
            'upsert_ai_key',
            {
                'p_user_id': user_id,
                'p_provider': provider,
                'p_api_key': api_key,
            },
        ).execute()

    def delete_key(self, user_id: str, provider: LLMProvider) -> None:
        self._client.rpc('delete_ai_key', {'p_user_id': user_id, 'p_provider': provider}).execute()

    def list_providers(self, user_id: str) -> list[LLMProvider]:
        response = self._client.rpc('list_ai_key_providers', {'p_user_id': user_id}).execute()
        rows = cast(list[dict[str, Any]], response.data)
        return [LLMProvider(row['provider']) for row in rows]


class FakeLLMKeyRepository(LLMKeyRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[str, LLMProvider], str] = {}

    def get_key(self, user_id: str, provider: LLMProvider) -> Optional[str]:
        return self._store.get((user_id, provider))

    def save_key(self, user_id: str, provider: LLMProvider, api_key: str) -> None:
        self._store[(user_id, provider)] = api_key

    def delete_key(self, user_id: str, provider: LLMProvider) -> None:
        self._store.pop((user_id, provider), None)

    def list_providers(self, user_id: str) -> list[LLMProvider]:
        return [provider for (uid, provider) in self._store if uid == user_id]
