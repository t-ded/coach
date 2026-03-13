from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

Role = Literal['user', 'assistant']


@dataclass(frozen=True, kw_only=True, slots=True)
class ChatTurn:
    role: Role
    content: str

    def render(self) -> str:
        return f'{self.role.capitalize()}: {self.content}'


class ChatHistory:
    def __init__(self, *, max_turns: int = 6) -> None:
        self._turns: deque[ChatTurn] = deque(maxlen=max_turns)

    def add(self, turn: ChatTurn) -> None:
        self._turns.append(turn)

    def render(self) -> str:
        lines: list[str] = [turn.render() for turn in self._turns]
        return '\n'.join(lines)

    def has_no_assistant_response(self) -> bool:
        return all(turn.role == 'user' for turn in self._turns)

    def clear(self) -> None:
        self._turns.clear()
