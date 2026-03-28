from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from typing import Optional

SessionType = Literal['unnamed', 'named']


@dataclass(frozen=True, kw_only=True, slots=True)
class Session:
    id: str
    user_id: str
    title: Optional[str]
    session_type: SessionType
    created_at: datetime
    last_message_at: datetime
    summarized_through_message_id: Optional[str] = None
    summary: Optional[str] = None


@dataclass(frozen=True, kw_only=True, slots=True)
class Message:
    id: str
    session_id: str
    role: Literal['user', 'assistant']
    content: str
    created_at: datetime
