from abc import ABC
from abc import abstractmethod
from functools import cached_property
from typing import Optional

import typer

from coach.domain.chat import ChatHistory
from coach.domain.chat import ChatTurn
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client


def _extend_parts(parts: list[str], part_title: str, content: Optional[str]) -> None:
    if content:
        parts.extend([part_title, content.strip()])


def build_assistant_prompt(
    *,
    system_prompt: str,
    user_system_prompt: Optional[str] = None,
    additional_context: Optional[str] = None,
    chat_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    parts: list[str] = [system_prompt.strip()]
    _extend_parts(parts, 'User instructions:', user_system_prompt)
    _extend_parts(parts, 'Additional context:', additional_context)
    _extend_parts(parts, 'Conversation so far:', chat_history)
    _extend_parts(parts, 'User question:', user_prompt)
    parts.append('Your answer: <response>')
    return '\n'.join(parts)


class Assistant(ABC):
    def __init__(self, provider: LLMProvider, model: Optional[str], max_history_turns: int = 10) -> None:
        self._llm_client = create_llm_client(provider=provider, model=model)
        self._history = ChatHistory(max_turns=max_history_turns)

    @property
    @abstractmethod
    def _response_label(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _system_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _user_system_prompt(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def _additional_context(self) -> Optional[str]:
        raise NotImplementedError

    def run_chat_loop(self) -> None:
        self._on_chat_start()
        while True:
            try:
                user_input = typer.prompt('You')
            except (EOFError, KeyboardInterrupt):
                typer.echo('\nGoodbye.')
                break
            typer.echo(f'\n{self._response_label}:\n')
            typer.echo(self._get_response(user_input))
            typer.echo('')

    def _on_chat_start(self) -> None:
        typer.echo(f'{self._response_label} ready. Type your responses (Ctrl+C to exit).\n')

    def _get_response(self, user_input: str) -> str:
        response = self._llm_client.complete(self._build_prompt(user_input))
        self._history.add(ChatTurn(role='user', content=user_input))
        self._history.add(ChatTurn(role='assistant', content=response))
        return response

    def _build_prompt(self, user_input: str) -> str:
        chat_history = None if self._history.has_no_assistant_response() else self._history.render()
        return build_assistant_prompt(
            system_prompt=self._system_prompt(),
            user_system_prompt=self._user_system_prompt(),
            additional_context=self._additional_context(),
            chat_history=chat_history,
            user_prompt=user_input,
        )
