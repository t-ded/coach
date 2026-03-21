from typing import Any
from typing import Optional
from typing import cast

from supabase import Client


class SupabaseUsersRepository:
    TABLE = 'users'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def get_display_name(self) -> Optional[str]:
        response = self._db.table(self.TABLE).select('display_name').eq('id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return cast(dict[str, Any], response.data).get('display_name')

    def set_display_name(self, display_name: str) -> None:
        self._db.table(self.TABLE).update({'display_name': display_name}).eq('id', self._user_id).execute()

    def get_strava_user_id(self) -> Optional[int]:
        response = self._db.table(self.TABLE).select('strava_user_id').eq('id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return cast(dict[str, Any], response.data).get('strava_user_id')

    def set_strava_user_id(self, strava_user_id: int) -> None:
        self._db.table(self.TABLE).update({'strava_user_id': strava_user_id}).eq('id', self._user_id).execute()
