from abc import ABC
from abc import abstractmethod
from typing import Optional

from coach.domain.chat import ChatHistory
from coach.domain.chat import ChatTurn
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client
from coach.utils import combine_sections


def build_assistant_prompt(
    *,
    system_prompt: str,
    user_system_prompt: Optional[str] = None,
    additional_context: Optional[str] = None,
    chat_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    sections = [
        ('System instructions:', system_prompt),
        ('User instructions:', user_system_prompt),
        ('Additional context:', additional_context),
        ('Conversation so far:', chat_history),
        ('User question:', user_prompt),
    ]
    parts = combine_sections(sections)
    parts.append('Your answer: <response>')
    return '\n'.join(parts)


class Assistant(ABC):
    def __init__(self, provider: LLMProvider, model: Optional[str], max_history_turns: int = 10) -> None:
        self._llm_client = create_llm_client(provider=provider, model=model)
        self._history = ChatHistory(max_turns=max_history_turns)

    @abstractmethod
    def _system_prompt(self) -> str:
        raise NotImplementedError

    def _user_system_prompt(self) -> Optional[str]:
        return None

    def _additional_context(self) -> Optional[str]:
        return None

    def get_response(self, user_input: str) -> str:
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
