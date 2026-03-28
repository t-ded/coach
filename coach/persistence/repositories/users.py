from datetime import datetime
from typing import Any
from typing import Optional
from typing import cast

from supabase import Client


class SupabaseUsersRepository:
    TABLE = 'users'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def _get_field(self, column: str) -> Optional[Any]:
        response = self._db.table(self.TABLE).select(column).eq('id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return cast(dict[str, Any], response.data).get(column)

    def _set_field(self, column: str, value: Any) -> None:
        self._db.table(self.TABLE).update({column: value}).eq('id', self._user_id).execute()

    def get_display_name(self) -> Optional[str]:
        return cast(Optional[str], self._get_field('display_name'))

    def set_display_name(self, display_name: str) -> None:
        self._set_field('display_name', display_name)

    def get_strava_user_id(self) -> Optional[int]:
        return cast(Optional[int], self._get_field('strava_user_id'))

    def set_strava_user_id(self, strava_user_id: int) -> None:
        self._set_field('strava_user_id', strava_user_id)

    def get_strava_user_id_and_display_name(self) -> tuple[Optional[int], Optional[str]]:
        response = self._db.table(self.TABLE).select('strava_user_id, display_name').eq('id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None, None
        data = cast(dict[str, Any], response.data)
        return cast(Optional[int], data.get('strava_user_id')), cast(Optional[str], data.get('display_name'))

    def get_last_strava_sync(self) -> Optional[datetime]:
        raw = self._get_field('last_strava_sync_at')
        return datetime.fromisoformat(cast(str, raw)) if raw else None

    def set_last_strava_sync(self, dt: datetime) -> None:
        self._set_field('last_strava_sync_at', dt.isoformat())
