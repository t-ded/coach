from dataclasses import dataclass

from supabase import Client

from coach.config.credentials import CredentialsStore
from coach.persistence.database import SupabaseDatabase


@dataclass(frozen=True)
class UserSession:
    client: Client
    user_id: str


def load_session() -> UserSession:
    stored = CredentialsStore().get_supabase_session()
    if stored is None:
        raise RuntimeError('Not logged in. Run "coach auth login" to authenticate.')

    client = SupabaseDatabase().client()
    response = client.auth.refresh_session(stored['refresh_token'])

    if response.session is None or response.user is None:
        raise RuntimeError('Session invalid or expired. Run "coach auth login" to re-authenticate.')

    # Persist refreshed tokens so the access_token stays current across runs
    CredentialsStore().store_supabase_session(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
    )

    return UserSession(client=client, user_id=response.user.id)
