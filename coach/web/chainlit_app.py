from datetime import datetime
from typing import Optional

import chainlit as cl
from supabase import Client

from coach.persistence.database import create_anon_client
from coach.persistence.database import create_secret_client
from coach.web.app import create_app
from coach.web.auth import build_authenticated_client
from coach.web.auth import refresh_if_needed
from coach.web.auth import sign_in_with_supabase
from coach.web.google_oauth import install_patched_google_provider
from coach.web.strava_oauth import generate_strava_auth_url

install_patched_google_provider()

# Mount the FastAPI OAuth callback on Chainlit's Starlette server
_fastapi_app = create_app()
cl.server.app.mount('/oauth', _fastapi_app)


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
    id_token: Optional[str] = None,  # never passed by Chainlit; we read from raw_user_data instead
) -> Optional[cl.User]:
    if provider_id != 'google':
        return None

    id_token = raw_user_data.get('id_token')  # noqa: S105
    if id_token is None:
        return None

    anon_client = create_anon_client()
    access_token, refresh_token, user_id, expires_at = sign_in_with_supabase(id_token, anon_client)

    default_user.metadata['supabase_access_token'] = access_token
    default_user.metadata['supabase_refresh_token'] = refresh_token
    default_user.metadata['supabase_user_id'] = user_id
    default_user.metadata['supabase_expires_at'] = expires_at.isoformat()

    return default_user


@cl.on_chat_start
async def on_chat_start() -> None:
    user: Optional[cl.User] = cl.user_session.get('user')
    if user is None:
        await cl.Message('Authentication error — please refresh and log in again.').send()
        return

    _init_user_session(user)

    user_id: str = cl.user_session.get('supabase_user_id')
    strava_user_id = _get_strava_user_id(user_id, _get_authenticated_client())

    if not strava_user_id:
        actions = [cl.Action(name='connect_strava', value='connect_strava', label='Connect Strava')]
        await cl.Message('To get started, please connect your Strava account.', actions=actions).send()
        return

    first_name = raw_user_data['given_name'] if (raw_user_data := user.metadata.get('raw_user_data')) else user.identifier.split('@')[0]
    await cl.Message(f'Hello, {first_name}. Coach is ready. What would you like to work on today?').send()


@cl.action_callback('connect_strava')
async def on_connect_strava(action: cl.Action) -> None:
    user_id: str = cl.user_session.get('supabase_user_id')
    url = generate_strava_auth_url(user_id, create_secret_client())
    await cl.Message(f'[Click here to connect Strava]({url})').send()


def _init_user_session(user: cl.User) -> None:
    metadata = user.metadata
    cl.user_session.set('supabase_access_token', metadata['supabase_access_token'])
    cl.user_session.set('supabase_refresh_token', metadata['supabase_refresh_token'])
    cl.user_session.set('supabase_user_id', metadata['supabase_user_id'])
    cl.user_session.set('supabase_expires_at', datetime.fromisoformat(metadata['supabase_expires_at']))


def _get_strava_user_id(user_id: str, client: Client) -> Optional[int]:
    result = client.table('users').select('strava_user_id').eq('id', user_id).maybe_single().execute()
    return result.data.get('strava_user_id') if result.data else None


def _get_authenticated_client() -> Client:
    access_token: str = cl.user_session.get('supabase_access_token')
    refresh_token: str = cl.user_session.get('supabase_refresh_token')
    expires_at: datetime = cl.user_session.get('supabase_expires_at')

    anon_client = create_anon_client()
    access_token, refresh_token, expires_at = refresh_if_needed(access_token, refresh_token, expires_at, anon_client)

    cl.user_session.set('supabase_access_token', access_token)
    cl.user_session.set('supabase_refresh_token', refresh_token)
    cl.user_session.set('supabase_expires_at', expires_at)

    return build_authenticated_client(access_token, refresh_token, anon_client)
