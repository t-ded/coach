import os

from supabase import Client
from supabase import create_client


class SupabaseDatabase:
    def __init__(self) -> None:
        url = os.environ['SUPABASE_URL']
        key = os.environ['SUPABASE_ANON_KEY']
        self._client: Client = create_client(url, key)

    def client(self) -> Client:
        return self._client
