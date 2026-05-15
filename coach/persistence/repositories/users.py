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

    @classmethod
    def find_user_id_by_strava_id(cls, client: Client, strava_athlete_id: int) -> Optional[str]:
        response = client.table(cls.TABLE).select('id').eq('strava_user_id', strava_athlete_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return cast(Optional[str], cast(dict[str, Any], response.data).get('id'))

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

    def clear_strava_user_id(self) -> None:
        self._set_field('strava_user_id', None)

    def get_strava_scope_warning(self) -> bool:
        return bool(self._get_field('strava_scope_warning'))

    def set_strava_scope_warning(self, warning: bool) -> None:
        self._set_field('strava_scope_warning', warning)

    def _get_datetime_field(self, column: str) -> Optional[datetime]:
        raw = self._get_field(column)
        return datetime.fromisoformat(cast(str, raw)) if raw else None

    def _set_datetime_field(self, column: str, dt: datetime) -> None:
        self._set_field(column, dt.isoformat())

    def get_last_strava_sync(self) -> Optional[datetime]:
        return self._get_datetime_field('last_strava_sync_at')

    def set_last_strava_sync(self, dt: datetime) -> None:
        self._set_datetime_field('last_strava_sync_at', dt)

    def get_email(self) -> Optional[str]:
        response = self._db.auth.admin.get_user_by_id(self._user_id)
        return response.user.email if response.user else None

    def get_email_notifications_enabled(self) -> bool:
        value = self._get_field('email_notifications_enabled')
        if value is None:
            return True
        return bool(value)

    def get_last_insight_email_at(self) -> Optional[datetime]:
        return self._get_datetime_field('last_insight_email_at')

    def set_last_insight_email_at(self, dt: datetime) -> None:
        self._set_datetime_field('last_insight_email_at', dt)

    def get_notification_context(self) -> tuple[bool, Optional[datetime], Optional[str]]:
        """Return (notifications_enabled, last_insight_email_at, display_name) in one query."""
        response = self._db.table(self.TABLE).select('email_notifications_enabled, last_insight_email_at, display_name').eq('id', self._user_id).maybe_single().execute()
        data = cast(dict[str, Any], response.data) if response and response.data else {}
        enabled_raw = data.get('email_notifications_enabled')
        enabled = bool(enabled_raw) if enabled_raw is not None else True
        last_raw = data.get('last_insight_email_at')
        last_sent = datetime.fromisoformat(cast(str, last_raw)) if last_raw else None
        display_name = cast(Optional[str], data.get('display_name'))
        return enabled, last_sent, display_name
