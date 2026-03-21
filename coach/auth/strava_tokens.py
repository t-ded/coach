from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Any
from typing import Optional
from typing import cast

from supabase import Client

from coach.config.credentials import CredentialsStore


@dataclass(slots=True)
class StravaTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime


class StravaTokenRepository(ABC):
    @abstractmethod
    def get_tokens(self, user_id: str) -> Optional[StravaTokens]: ...

    @abstractmethod
    def save_tokens(self, user_id: str, tokens: StravaTokens) -> None: ...


class SupabaseStravaTokenRepository(StravaTokenRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def get_tokens(self, user_id: str) -> Optional[StravaTokens]:
        response = self._client.rpc('get_strava_tokens', {'p_user_id': user_id}).execute()
        rows = cast(list[dict[str, Any]], response.data)
        if not rows:
            return None
        row = rows[0]
        return StravaTokens(
            access_token=row['access_token'],
            refresh_token=row['refresh_token'],
            expires_at=datetime.fromisoformat(row['expires_at']),
        )

    def save_tokens(self, user_id: str, tokens: StravaTokens) -> None:
        self._client.rpc('upsert_strava_tokens', {
            'p_user_id': user_id,
            'p_access_token': tokens.access_token,
            'p_refresh_token': tokens.refresh_token,
            'p_expires_at': tokens.expires_at.isoformat(),
        }).execute()


class CredentialsStoreStravaTokenRepository(StravaTokenRepository):
    def __init__(self, store: Optional[CredentialsStore] = None) -> None:
        self._store = store or CredentialsStore()

    def get_tokens(self, user_id: str) -> Optional[StravaTokens]:
        credentials = self._store.get_strava_credentials()
        if not credentials:
            return None
        return StravaTokens(
            access_token=credentials['access_token'],
            refresh_token=credentials['refresh_token'],
            expires_at=datetime.fromtimestamp(credentials['expires_at'], tz=UTC),
        )

    def save_tokens(self, user_id: str, tokens: StravaTokens) -> None:
        existing = self._store.get_strava_credentials() or {}
        self._store.store_strava_credentials(
            client_id=existing.get('client_id', ''),
            client_secret=existing.get('client_secret', ''),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_at=int(tokens.expires_at.timestamp()),
        )
