import html as html_module
import os
import secrets
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Annotated
from typing import Any
from typing import Optional
from typing import Union
from typing import cast

import requests
import requests.exceptions
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from supabase import Client

from coach.auth.llm_keys import SupabaseLLMKeyRepository
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import display_provider

router = APIRouter()

_STATE_TABLE = 'api_key_setup_state'
_STATE_EXPIRY_MINUTES = 10
_CHAINLIT_URL_DEFAULT = 'http://localhost:8000'
_GOOGLE_VALIDATE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
_OPENAI_VALIDATE_URL = 'https://api.openai.com/v1/models'

_SecretClient = Annotated[Client, Depends(create_secret_client)]


def generate_api_key_form_url(user_id: str, secret_client: Client, provider: Optional[str] = None) -> str:
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=_STATE_EXPIRY_MINUTES)
    secret_client.table(_STATE_TABLE).insert(
        {
            'user_id': user_id,
            'state': state,
            'expires_at': expires_at.isoformat(),
        },
    ).execute()
    base_url = os.environ.get('CHAINLIT_URL', _CHAINLIT_URL_DEFAULT)
    url = f'{base_url}/oauth/api-key?state={state}'
    if provider:
        url += f'&provider={provider}'
    return url


def _lookup_state(state: str, secret_client: Client) -> str:
    result = secret_client.table(_STATE_TABLE).select('user_id, expires_at').eq('state', state).execute()
    rows = cast(list[dict[str, Any]], result.data)
    if not rows:
        raise HTTPException(status_code=400, detail='Invalid or missing state')
    row = rows[0]
    expires_at = datetime.fromisoformat(row['expires_at'])
    if datetime.now(UTC) > expires_at:
        secret_client.table(_STATE_TABLE).delete().eq('state', state).execute()
        raise HTTPException(status_code=400, detail='State has expired')
    return cast(str, row['user_id'])


def _consume_state(state: str, secret_client: Client) -> None:
    secret_client.table(_STATE_TABLE).delete().eq('state', state).execute()


def _validate_api_key(provider: LLMProvider, api_key: str) -> bool:
    try:
        if provider == LLMProvider.GOOGLE:
            response = requests.get(_GOOGLE_VALIDATE_URL, params={'key': api_key}, timeout=5)
        else:
            response = requests.get(_OPENAI_VALIDATE_URL, headers={'Authorization': f'Bearer {api_key}'}, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _render_form(state: str, error: Optional[str] = None, selected_provider: str = 'google') -> HTMLResponse:
    error_html = f'<p class="error">{html_module.escape(error)}</p>' if error else ''
    google_selected = 'selected' if selected_provider == 'google' else ''
    openai_selected = 'selected' if selected_provider == 'openai' else ''
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connect AI Provider — Running Coach</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 480px; margin: 4rem auto; padding: 0 1.5rem; color: #1a1a1a; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.5rem; }}
    .intro {{ color: #555; margin-bottom: 1.5rem; font-size: 0.95rem; }}
    .error {{ color: #c0392b; background: #fdf0ed; border: 1px solid #e8bdb5; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.9rem; }}
    label {{ display: block; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.4rem; }}
    select, input[type="password"] {{ width: 100%; padding: 0.6rem 0.8rem; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; box-sizing: border-box; margin-bottom: 1rem; }}
    button {{ width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }}
    button:hover {{ background: #1d4ed8; }}
    .hint {{ font-size: 0.82rem; color: #666; margin-top: -0.75rem; margin-bottom: 1rem; }}
    a {{ color: #2563eb; }}
  </style>
</head>
<body>
  <h1>Connect your AI provider</h1>
  <p class="intro">The app uses a language model to power your coaching chat. You need to provide an API key from one of the supported providers. Only one key is required to get started.</p>
  {error_html}
  <form method="post" action="/oauth/api-key/store">
    <input type="hidden" name="state" value="{html_module.escape(state)}">

    <label for="provider">Provider</label>
    <select name="provider" id="provider">
      <option value="google" {google_selected}>Google AI Studio (free tier available)</option>
      <option value="openai" {openai_selected}>OpenAI</option>
    </select>

    <label for="api_key">API key</label>
    <input type="password" name="api_key" id="api_key" placeholder="Paste your API key here" autocomplete="off" required>
    <p class="hint">
      Get a free Google AI Studio key at <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a>.
      OpenAI keys are at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com/api-keys</a>.
    </p>

    <button type="submit">Save and continue</button>
  </form>
</body>
</html>"""
    return HTMLResponse(content=content)


@router.get('/api-key')
def api_key_form(
    secret_client: _SecretClient,
    state: str,
    error: Optional[str] = None,
    provider: Optional[str] = None,
) -> HTMLResponse:
    _lookup_state(state, secret_client)
    return _render_form(state, error, selected_provider=provider or 'google')


@router.post('/api-key/store', response_model=None)
def api_key_store(
    secret_client: _SecretClient,
    state: str = Form(...),
    provider: str = Form(...),
    api_key: str = Form(...),
) -> Union[RedirectResponse, HTMLResponse]:
    user_id = _lookup_state(state, secret_client)

    try:
        llm_provider = LLMProvider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'Unknown provider: {provider}') from exc

    if not _validate_api_key(llm_provider, api_key):
        error_msg = f'The {display_provider(llm_provider)} key could not be verified. Please check it and try again.'
        return _render_form(state, error_msg, selected_provider=provider)

    key_repo = SupabaseLLMKeyRepository(secret_client)
    is_first_key = not key_repo.list_providers(user_id)
    key_repo.save_key(user_id, llm_provider, api_key)

    if is_first_key:
        SupabaseUserProfileRepository(secret_client, user_id).set_preferred_provider(llm_provider)

    _consume_state(state, secret_client)

    return RedirectResponse(os.environ.get('CHAINLIT_URL', _CHAINLIT_URL_DEFAULT), status_code=303)
