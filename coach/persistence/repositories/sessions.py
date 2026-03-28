from datetime import UTC
from datetime import datetime
from typing import Any
from typing import Optional
from typing import cast

from postgrest import SyncRequestBuilder
from supabase import Client

from coach.domain.session import Session
from coach.domain.session import SessionType
from coach.utils import parse_utc_datetime

type SessionRow = dict[str, Any]

MAX_UNNAMED_SESSIONS = 3
MAX_NAMED_SESSIONS = 5


class SupabaseSessionRepository:
    TABLE = 'sessions'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def _table(self) -> SyncRequestBuilder:
        return self._db.table(self.TABLE)

    def create(self, *, session_type: SessionType = 'unnamed', title: Optional[str] = None) -> Session:
        self._enforce_cap(session_type)
        row: SessionRow = {'user_id': self._user_id, 'session_type': session_type}
        if title is not None:
            row['title'] = title
        response = self._table().insert(row).execute()
        return self._from_row(cast(SessionRow, response.data[0]))

    def get(self, session_id: str) -> Optional[Session]:
        response = self._table().select('*').eq('id', session_id).eq('user_id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return self._from_row(cast(SessionRow, response.data))

    def list_for_user(self) -> list[Session]:
        response = self._table().select('*').eq('user_id', self._user_id).order('last_message_at', desc=True).execute()
        return [self._from_row(cast(SessionRow, row)) for row in response.data]

    def update_title(self, session_id: str, title: str) -> None:
        self._table().update({'title': title}).eq('id', session_id).eq('user_id', self._user_id).execute()

    def update_last_message_at(self, session_id: str) -> None:
        self._table().update({'last_message_at': datetime.now(tz=UTC).isoformat()}).eq('id', session_id).eq('user_id', self._user_id).execute()

    def promote(self, session_id: str, title: Optional[str] = None) -> None:
        self._enforce_cap('named')
        update: SessionRow = {'session_type': 'named'}
        if title is not None:
            update['title'] = title
        self._table().update(update).eq('id', session_id).eq('user_id', self._user_id).execute()

    def update_summary(self, session_id: str, summary: str, through_message_id: str) -> None:
        self._table().update(
            {
                'summary': summary,
                'summarized_through_message_id': through_message_id,
            },
        ).eq('id', session_id).eq('user_id', self._user_id).execute()

    def delete(self, session_id: str) -> None:
        self._table().delete().eq('id', session_id).eq('user_id', self._user_id).execute()

    def _enforce_cap(self, session_type: SessionType) -> None:
        cap = MAX_NAMED_SESSIONS if session_type == 'named' else MAX_UNNAMED_SESSIONS
        response = self._table().select('id').eq('user_id', self._user_id).eq('session_type', session_type).order('last_message_at', desc=True).execute()
        ids_to_delete = [cast(SessionRow, row)['id'] for row in response.data[cap - 1 :]]
        for session_id in ids_to_delete:
            self._table().delete().eq('id', session_id).eq('user_id', self._user_id).execute()

    @staticmethod
    def _from_row(row: SessionRow) -> Session:
        return Session(
            id=row['id'],
            user_id=row['user_id'],
            title=row.get('title'),
            session_type=row['session_type'],
            created_at=parse_utc_datetime(row['created_at']),
            last_message_at=parse_utc_datetime(row['last_message_at']),
            summarized_through_message_id=row.get('summarized_through_message_id'),
            summary=row.get('summary'),
        )
