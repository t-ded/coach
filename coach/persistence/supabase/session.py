import os
from dataclasses import dataclass

from supabase import Client

from coach.persistence.supabase.database import SupabaseDatabase


@dataclass(frozen=True)
class UserSession:
    client: Client
    user_id: str


def load_session() -> UserSession:
    # user_id is sourced from env for now.
    # When Supabase Auth (Google OAuth) is wired in, this will be replaced by
    # client.auth.sign_in_with_oauth() → client.auth.get_user().user.id
    # without changing any call sites.
    user_id = os.environ['SUPABASE_USER_ID']
    client = SupabaseDatabase().client()
    return UserSession(client=client, user_id=user_id)
