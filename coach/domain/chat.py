from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from typing import Any
from typing import Literal
from typing import Optional


@dataclass(frozen=True, kw_only=True, slots=True)
class CoachResponse:
    summary: str
    observations: list[str] = field(metadata={'bullets': True})
    recommendations: list[str] = field(metadata={'bullets': True})
    confidence_notes: Optional[str] = field(default=None, metadata={'optional': True})

    @classmethod
    def headers(cls) -> list[str]:
        return [f'{f.name.replace('_', ' ').title()}' for f in fields(cls)]

    @classmethod
    def field_info(cls) -> dict[str, dict[str, Any]]:
        return {f.name: dict(f.metadata) for f in fields(cls)}


Role = Literal['user', 'coach']


@dataclass(frozen=True, kw_only=True, slots=True)
class ChatTurn:
    role: Role
    content: str


class ChatHistory:
    def __init__(self, *, max_turns: int = 6) -> None:
        self._turns: deque[ChatTurn] = deque(maxlen=max_turns)

    def add(self, turn: ChatTurn) -> None:
        self._turns.append(turn)

    def render(self) -> str:
        lines: list[str] = []

        for turn in self._turns:
            prefix = turn.role.capitalize()
            lines.append(f'{prefix}: {turn.content}')

        return '\n'.join(lines)

    def has_no_coach_response(self) -> bool:
        return all(turn.role == 'user' for turn in self._turns)
