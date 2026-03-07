from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Optional

import requests

from coach.auth.setup.strava import STRAVA_OAUTH_ENDPOINT
from coach.auth.utils import no_credentials_found_message
from coach.config.credentials import CredentialsStore


@dataclass(slots=True)
class StravaAccessToken:
    token: str
    expires_at: datetime


class StravaAuth:
    def __init__(self) -> None:
        self._store = CredentialsStore()
        self._access_token: Optional[StravaAccessToken] = None

    def get_access_token(self) -> str:
        if self._access_token and not self._is_expired():
            return self._access_token.token

        self._refresh_access_token()
        return self._access_token.token  # type: ignore[union-attr]

    def _is_expired(self) -> bool:
        return datetime.now(UTC) >= self._access_token.expires_at  # type: ignore[union-attr]

    def _refresh_access_token(self) -> None:
        credentials = self._store.get_strava_credentials()
        if not credentials:
            msg = no_credentials_found_message('Strava')
            raise RuntimeError(msg)

        response = requests.post(
            STRAVA_OAUTH_ENDPOINT,
            data={
                'client_id': credentials['client_id'],
                'client_secret': credentials['client_secret'],
                'refresh_token': credentials['refresh_token'],
                'grant_type': 'refresh_token',
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        if 'access_token' not in payload:
            raise RuntimeError(f'Strava token refresh failed: {payload}')

        self._store.store_strava_credentials(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            access_token=payload['access_token'],
            refresh_token=payload['refresh_token'],
            expires_at=payload['expires_at'],
        )

        self._access_token = StravaAccessToken(
            token=payload['access_token'],
            expires_at=datetime.fromtimestamp(payload['expires_at'], tz=UTC),
        )
