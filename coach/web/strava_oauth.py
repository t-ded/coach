import os
import secrets
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import cast
from urllib.parse import urlencode

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from supabase import Client

from coach.auth.strava import STRAVA_AUTHORIZE_URL
from coach.auth.strava import STRAVA_OAUTH_ENDPOINT
from coach.auth.strava_tokens import StravaTokens
from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.users import SupabaseUsersRepository

router = APIRouter()

_STRAVA_REDIRECT_URI = os.environ.get('STRAVA_REDIRECT_URI', 'http://localhost:8000/oauth/auth/strava/callback')
_STATE_EXPIRY_MINUTES = 10


def generate_strava_auth_url(user_id: str, secret_client: Client) -> str:
    """Insert a CSRF state row and return the Strava authorization URL."""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=_STATE_EXPIRY_MINUTES)

    secret_client.table('strava_oauth_state').insert(
        {
            'user_id': user_id,
            'state': state,
            'expires_at': expires_at.isoformat(),
        },
    ).execute()

    return f'{STRAVA_AUTHORIZE_URL}?{
        urlencode(
            {
                "client_id": os.environ["STRAVA_CLIENT_ID"],
                "redirect_uri": _STRAVA_REDIRECT_URI,
                "response_type": "code",
                "scope": "activity:read_all",
                "state": state,
            }
        )
    }'


def _exchange_code_for_tokens(code: str, redirect_uri: str) -> dict[str, Any]:
    response = requests.post(
        STRAVA_OAUTH_ENDPOINT,
        data={
            'client_id': os.environ['STRAVA_CLIENT_ID'],
            'client_secret': os.environ['STRAVA_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _validate_and_consume_state(state: str, secret_client: Client) -> str:
    query_result = secret_client.table('strava_oauth_state').select('user_id, expires_at').eq('state', state).execute()
    rows = cast(list[dict[str, Any]], query_result.data)

    if not rows:
        raise HTTPException(status_code=400, detail='Invalid or missing state')

    row = rows[0]
    secret_client.table('strava_oauth_state').delete().eq('state', state).execute()

    expires_at = datetime.fromisoformat(row['expires_at'])
    if datetime.now(UTC) > expires_at:
        raise HTTPException(status_code=400, detail='State has expired')

    return cast(str, row['user_id'])


@router.get('/auth/strava/callback')
def strava_oauth_callback(
    code: str,
    state: str,
    scope: str = '',
    secret_client: Client = Depends(create_secret_client),  # noqa: B008
) -> RedirectResponse:
    user_id = _validate_and_consume_state(state, secret_client)
    token_data = _exchange_code_for_tokens(code, _STRAVA_REDIRECT_URI)

    tokens = StravaTokens(
        access_token=token_data['access_token'],
        refresh_token=token_data['refresh_token'],
        expires_at=datetime.fromtimestamp(token_data['expires_at'], tz=UTC),
    )
    SupabaseStravaTokenRepository(secret_client).save_tokens(user_id, tokens)

    strava_athlete_id: int = token_data['athlete']['id']
    users_repo = SupabaseUsersRepository(secret_client, user_id)
    users_repo.set_strava_user_id(strava_athlete_id)

    granted_scopes = {s.strip() for s in scope.split(',')}
    if 'activity:read_all' not in granted_scopes:
        users_repo.set_strava_scope_warning(True)

    chainlit_url = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
    return RedirectResponse(chainlit_url)
