import os
from datetime import UTC
from datetime import datetime
from typing import Optional

import requests

from coach.auth.strava_tokens import StravaTokenRepository
from coach.auth.strava_tokens import StravaTokens

STRAVA_AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_OAUTH_ENDPOINT = 'https://www.strava.com/oauth/token'


class StravaAuth:
    # Refresh tokens proactively this many seconds before actual expiry.
    # Strava issues rotating refresh tokens — once used, the old one is immediately
    # invalidated. Refreshing early prevents the race condition where two concurrent
    # requests both see an expired token and both attempt a refresh, causing the
    # second one to receive "Invalid Refresh Token: Already Used".
    _EXPIRY_BUFFER_SECONDS = 5 * 60

    def __init__(self, user_id: str, token_repo: StravaTokenRepository) -> None:
        self._user_id = user_id
        self._token_repo = token_repo
        self._cached: Optional[StravaTokens] = None

    def get_access_token(self) -> str:
        if self._cached is not None and not self._is_near_expiry(self._cached):
            return self._cached.access_token

        tokens = self._token_repo.get_tokens(self._user_id)
        if tokens is None:
            raise RuntimeError('No Strava credentials found.')

        if self._is_near_expiry(tokens):
            tokens = self._refresh(tokens)

        self._cached = tokens
        return tokens.access_token

    def _is_near_expiry(self, tokens: StravaTokens) -> bool:
        return datetime.now(UTC).timestamp() >= tokens.expires_at.timestamp() - self._EXPIRY_BUFFER_SECONDS

    def _refresh(self, tokens: StravaTokens) -> StravaTokens:
        from coach.ingestion.strava.client import StravaTokenRevokedError

        client_id = os.environ.get('STRAVA_CLIENT_ID', '')
        client_secret = os.environ.get('STRAVA_CLIENT_SECRET', '')

        response = requests.post(
            STRAVA_OAUTH_ENDPOINT,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': tokens.refresh_token,
                'grant_type': 'refresh_token',
            },
            timeout=10,
        )

        if response.status_code in (400, 401):
            raise StravaTokenRevokedError('Strava refresh token is invalid or has been revoked.')

        response.raise_for_status()
        payload = response.json()

        if 'access_token' not in payload:
            raise RuntimeError(f'Strava token refresh failed: {payload}')

        refreshed = StravaTokens(
            access_token=payload['access_token'],
            refresh_token=payload['refresh_token'],
            expires_at=datetime.fromtimestamp(payload['expires_at'], tz=UTC),
        )
        self._token_repo.save_tokens(self._user_id, refreshed)
        return refreshed
