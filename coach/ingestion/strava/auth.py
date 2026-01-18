from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Optional

import requests

from coach.config.settings import load_strava_settings


@dataclass(slots=True)
class StravaAccessToken:
    token: str
    expires_at: datetime


class StravaAuth:
    def __init__(self) -> None:
        self._settings = load_strava_settings()
        self._access_token: Optional[StravaAccessToken] = None

    def get_access_token(self) -> str:
        if self._access_token is not None and not self._is_expired():
            return self._access_token.token

        self._refresh_access_token()
        return self._access_token.token  # type: ignore[union-attr]

    def _is_expired(self) -> bool:
        return datetime.now(UTC) >= self._access_token.expires_at  # type: ignore[union-attr]

    def _refresh_access_token(self) -> None:
        response = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': self._settings.client_id,
                'client_secret': self._settings.client_secret,
                'refresh_token': self._settings.refresh_token,
                'grant_type': 'refresh_token',
            },
            timeout=10,
        )
        response.raise_for_status()

        payload = response.json()
        if 'access_token' not in payload:
            raise RuntimeError(f'Strava token refresh failed: {payload}')

        self._access_token = StravaAccessToken(
            token=payload['access_token'],
            expires_at=datetime.fromtimestamp(payload['expires_at'], tz=UTC),
        )
