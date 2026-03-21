from datetime import datetime
from typing import Optional

import chainlit as cl
from supabase import Client
from supabase import create_client

from coach.persistence.database import SUPABASE_ANON_KEY
from coach.persistence.database import SUPABASE_URL
from coach.web.app import create_app
from coach.web.auth import build_authenticated_client
from coach.web.auth import refresh_if_needed
from coach.web.auth import sign_in_with_supabase

# Mount the FastAPI OAuth callback on Chainlit's Starlette server
_fastapi_app = create_app()
cl.server.app.mount('/oauth', _fastapi_app)


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
    id_token: Optional[str] = None,
) -> Optional[cl.User]:
    if provider_id != 'google' or id_token is None:
        return None

    anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
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

    metadata = user.metadata
    cl.user_session.set('supabase_access_token', metadata['supabase_access_token'])
    cl.user_session.set('supabase_refresh_token', metadata['supabase_refresh_token'])
    cl.user_session.set('supabase_user_id', metadata['supabase_user_id'])
    cl.user_session.set('supabase_expires_at', datetime.fromisoformat(metadata['supabase_expires_at']))

    first_name = raw_user_data['given_name'] if (raw_user_data := user.metadata.get('raw_user_data')) else user.identifier.split('@')[0]
    await cl.Message(f'Hello, {first_name}. Coach is ready. What would you like to work on today?').send()


def _get_authenticated_client() -> Client:
    access_token: str = cl.user_session.get('supabase_access_token')
    refresh_token: str = cl.user_session.get('supabase_refresh_token')
    expires_at: datetime = cl.user_session.get('supabase_expires_at')

    anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    access_token, refresh_token, expires_at = refresh_if_needed(access_token, refresh_token, expires_at, anon_client)

    cl.user_session.set('supabase_access_token', access_token)
    cl.user_session.set('supabase_refresh_token', refresh_token)
    cl.user_session.set('supabase_expires_at', expires_at)

    return build_authenticated_client(access_token, refresh_token, anon_client)
