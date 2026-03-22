from datetime import datetime

import chainlit as cl
from supabase import Client

from coach.persistence.database import create_anon_client
from coach.web.auth import build_authenticated_client
from coach.web.auth import refresh_if_needed

SESSION_ACCESS_TOKEN = 'supabase_access_token'  # noqa: S105
SESSION_REFRESH_TOKEN = 'supabase_refresh_token'  # noqa: S105
SESSION_USER_ID = 'supabase_user_id'
SESSION_EXPIRES_AT = 'supabase_expires_at'


def init_user_session(user: cl.User) -> None:
    metadata = user.metadata
    cl.user_session.set(SESSION_ACCESS_TOKEN, metadata[SESSION_ACCESS_TOKEN])
    cl.user_session.set(SESSION_REFRESH_TOKEN, metadata[SESSION_REFRESH_TOKEN])
    cl.user_session.set(SESSION_USER_ID, metadata[SESSION_USER_ID])
    cl.user_session.set(SESSION_EXPIRES_AT, datetime.fromisoformat(metadata[SESSION_EXPIRES_AT]))


def get_authenticated_client() -> Client:
    access_token: str = cl.user_session.get(SESSION_ACCESS_TOKEN)
    refresh_token: str = cl.user_session.get(SESSION_REFRESH_TOKEN)
    expires_at: datetime = cl.user_session.get(SESSION_EXPIRES_AT)

    anon_client = create_anon_client()
    access_token, refresh_token, expires_at = refresh_if_needed(access_token, refresh_token, expires_at, anon_client)

    cl.user_session.set(SESSION_ACCESS_TOKEN, access_token)
    cl.user_session.set(SESSION_REFRESH_TOKEN, refresh_token)
    cl.user_session.set(SESSION_EXPIRES_AT, expires_at)

    return build_authenticated_client(access_token, refresh_token, anon_client)


def get_user_id() -> str:
    return cl.user_session.get(SESSION_USER_ID)
