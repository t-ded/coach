from supabase import Client


class SupabaseUsersRepository:
    TABLE = 'users'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def set_strava_user_id(self, strava_user_id: int) -> None:
        self._db.table(self.TABLE).update({'strava_user_id': strava_user_id}).eq('id', self._user_id).execute()
