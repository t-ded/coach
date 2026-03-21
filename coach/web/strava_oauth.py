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
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from supabase import Client
from supabase import create_client

from coach.auth.setup.strava import STRAVA_AUTHORIZE_URL
from coach.auth.setup.strava import STRAVA_OAUTH_ENDPOINT
from coach.auth.strava_tokens import StravaTokens
from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.persistence.database import SUPABASE_ANON_KEY
from coach.persistence.database import SUPABASE_URL

router = APIRouter()

_STRAVA_REDIRECT_URI = os.environ.get('STRAVA_REDIRECT_URI', 'http://localhost:8000/auth/strava/callback')
_STATE_EXPIRY_MINUTES = 10


def get_anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_secret_client() -> Client:
    secret_key = os.environ['SUPABASE_SECRET_KEY']
    return create_client(SUPABASE_URL, secret_key)


def get_current_user_id(request: Request, anon_client: Client = Depends(get_anon_client)) -> str:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing authorization header')
    jwt = auth_header[len('Bearer '):]
    auth_response = anon_client.auth.get_user(jwt)
    if not auth_response or not auth_response.user:
        raise HTTPException(status_code=401, detail='Invalid session')
    return str(auth_response.user.id)


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


@router.get('/auth/strava')
def initiate_strava_oauth(
    user_id: str = Depends(get_current_user_id),
    secret_client: Client = Depends(get_secret_client),
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=_STATE_EXPIRY_MINUTES)

    secret_client.table('strava_oauth_state').insert({
        'user_id': user_id,
        'state': state,
        'expires_at': expires_at.isoformat(),
    }).execute()

    auth_url = f'{STRAVA_AUTHORIZE_URL}?{urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "redirect_uri": _STRAVA_REDIRECT_URI,
        "response_type": "code",
        "scope": "activity:read_all",
        "state": state,
    })}'

    return RedirectResponse(auth_url)


@router.get('/auth/strava/callback')
def strava_oauth_callback(
    code: str,
    state: str,
    secret_client: Client = Depends(get_secret_client),
) -> HTMLResponse:
    query_result = secret_client.table('strava_oauth_state').select('*').eq('state', state).execute()
    rows = cast(list[dict[str, Any]], query_result.data)

    if not rows:
        raise HTTPException(status_code=400, detail='Invalid or missing state')

    row = rows[0]
    expires_at = datetime.fromisoformat(row['expires_at'])

    if datetime.now(UTC) > expires_at:
        secret_client.table('strava_oauth_state').delete().eq('state', state).execute()
        raise HTTPException(status_code=400, detail='State has expired')

    user_id: str = row['user_id']
    secret_client.table('strava_oauth_state').delete().eq('state', state).execute()

    token_data = _exchange_code_for_tokens(code, _STRAVA_REDIRECT_URI)

    tokens = StravaTokens(
        access_token=token_data['access_token'],
        refresh_token=token_data['refresh_token'],
        expires_at=datetime.fromtimestamp(token_data['expires_at'], tz=UTC),
    )
    SupabaseStravaTokenRepository(secret_client).save_tokens(user_id, tokens)

    strava_athlete_id: int = token_data['athlete']['id']
    secret_client.table('users').update({'strava_user_id': strava_athlete_id}).eq('id', user_id).execute()

    # TODO: redirect to Chainlit chat URL once available
    return HTMLResponse(content=_success_html())


def _success_html() -> str:
    return '''<!DOCTYPE html>
<html><body>
<h1>Strava Connected!</h1>
<p>Your Strava account has been successfully connected. You can close this window.</p>
</body></html>'''
