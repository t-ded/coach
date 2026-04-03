from collections.abc import Iterable
from datetime import UTC
from datetime import datetime
from typing import Any
from typing import Optional
from typing import cast

from postgrest import CountMethod
from postgrest import SyncRequestBuilder

from coach.domain.activity import Activity
from coach.persistence.repository_interface import Repository
from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import serialize_activity
from supabase import Client

type ActivityRow = dict[str, Any]


class SupabaseActivityRepository(Repository[Activity]):
    TABLE = 'activities'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def _table(self) -> SyncRequestBuilder:
        return self._db.table(self.TABLE)

    def save(self, activity: Activity) -> None:
        self._save_query(self._to_row(activity))

    def save_many(self, activities: Iterable[Activity]) -> None:
        rows = [self._to_row(a) for a in activities]
        if rows:
            self._save_query(rows)

    def _save_query(self, to_save: ActivityRow | list[ActivityRow]) -> None:
        self._table().upsert(to_save, on_conflict='id').execute()

    def list_all(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[Activity]:
        query = self._table().select('*').eq(column='user_id', value=self._user_id)
        if start_date:
            query = query.gte('start_time_utc', start_date)
        if end_date:
            query = query.lt('start_time_utc', end_date)

        response = query.execute()
        return [deserialize_activity(cast(ActivityRow, row)) for row in response.data]

    def count(self) -> int:
        response = self._table().select('id', count=CountMethod.exact).eq(column='user_id', value=self._user_id).execute()
        return response.count or 0

    def last_activity_timestamp(self) -> Optional[int]:
        response = self._table().select('start_time_utc').order('start_time_utc', desc=True).eq(column='user_id', value=self._user_id).limit(1).execute()
        if not response.data:
            return None
        row = cast(ActivityRow, response.data[0])
        return int(datetime.fromisoformat(cast(str, row['start_time_utc'])).timestamp())

    # Re-fetch a 2-week window before the last known activity to catch backdated
    # or edited activities added since the previous sync.
    _SYNC_LOOKBACK_SECONDS = 2 * 7 * 24 * 60 * 60

    def sync_cursor(self) -> int:
        last = self.last_activity_timestamp()
        if last is None or last < self._SYNC_LOOKBACK_SECONDS:
            return 0
        return last - self._SYNC_LOOKBACK_SECONDS

    def existing_ids(self, after: int) -> set[int]:
        dt = datetime.fromtimestamp(after, tz=UTC).isoformat()
        response = self._table().select('id').eq('user_id', self._user_id).gte('start_time_utc', dt).execute()
        return {cast(ActivityRow, row)['id'] for row in response.data}

    def reset_table(self) -> None:
        self._table().delete().eq(column='user_id', value=self._user_id).execute()

    def delete_all_for_user(self) -> None:
        self._table().delete().eq(column='user_id', value=self._user_id).execute()

    def delete_by_strava_id(self, strava_activity_id: int) -> None:
        self._table().delete().eq(column='id', value=strava_activity_id).eq(column='user_id', value=self._user_id).execute()

    def _to_row(self, activity: Activity) -> ActivityRow:
        row = serialize_activity(activity)
        row['user_id'] = self._user_id
        return row
