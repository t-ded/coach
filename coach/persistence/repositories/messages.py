from typing import Any
from typing import Optional
from typing import cast

from postgrest import SyncRequestBuilder
from supabase import Client

from coach.domain.chat import Role
from coach.domain.session import Message
from coach.utils import parse_utc_datetime

type MessageRow = dict[str, Any]


class SupabaseMessageRepository:
    TABLE = 'messages'

    def __init__(self, client: Client) -> None:
        self._db = client

    def _table(self) -> SyncRequestBuilder:
        return self._db.table(self.TABLE)

    def save(self, session_id: str, role: Role, content: str) -> Message:
        row: MessageRow = {'session_id': session_id, 'role': role, 'content': content}
        response = self._table().insert(row).execute()
        return self._from_row(cast(MessageRow, response.data[0]))

    def load_for_session(self, session_id: str) -> list[Message]:
        response = self._table().select('*').eq('session_id', session_id).order('created_at', desc=False).execute()
        return [self._from_row(cast(MessageRow, row)) for row in response.data]

    def latest_id(self, session_id: str) -> Optional[str]:
        response = self._table().select('id').eq('session_id', session_id).order('created_at', desc=True).limit(1).execute()
        if not response.data:
            return None
        return cast(str, cast(MessageRow, response.data[0])['id'])

    @staticmethod
    def _from_row(row: MessageRow) -> Message:
        return Message(
            id=row['id'],
            session_id=row['session_id'],
            role=row['role'],
            content=row['content'],
            created_at=parse_utc_datetime(row['created_at']),
        )
