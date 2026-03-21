from datetime import UTC
from datetime import datetime
from datetime import timedelta

from supabase import Client

_REFRESH_THRESHOLD_MINUTES = 5


def sign_in_with_supabase(id_token: str, client: Client) -> tuple[str, str, str, datetime]:
    """Exchange a Google ID token for a Supabase session.

    Returns (access_token, refresh_token, user_id, expires_at).
    """
    response = client.auth.sign_in_with_id_token({'provider': 'google', 'token': id_token})
    session = response.session
    user = response.user
    if session is None or user is None:
        raise RuntimeError('Supabase sign-in failed: no session returned')
    return (
        session.access_token,
        session.refresh_token,
        str(user.id),
        datetime.fromtimestamp(session.expires_at or 0, tz=UTC),
    )


def refresh_if_needed(access_token: str, refresh_token: str, expires_at: datetime, client: Client) -> tuple[str, str, datetime]:
    """Return current or refreshed (access_token, refresh_token, expires_at).

    Refreshes transparently when within 5 minutes of expiry.
    """
    if datetime.now(UTC) < expires_at - timedelta(minutes=_REFRESH_THRESHOLD_MINUTES):
        return access_token, refresh_token, expires_at

    response = client.auth.refresh_session(refresh_token)
    session = response.session
    if session is None:
        raise RuntimeError('Supabase token refresh failed: no session returned')
    return (
        session.access_token,
        session.refresh_token,
        datetime.fromtimestamp(session.expires_at or 0, tz=UTC),
    )


def build_authenticated_client(access_token: str, refresh_token: str, base_client: Client) -> Client:
    """Set the user's JWT on a Supabase client so RLS resolves auth.uid() correctly."""
    base_client.auth.set_session(access_token=access_token, refresh_token=refresh_token)
    return base_client
