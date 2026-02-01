from coach.domain.chat import ChatHistory
from coach.domain.chat import ChatTurn


class TestChatHistory:
    def setup_method(self) -> None:
        self._history = ChatHistory(max_turns=2)

    def test_is_empty(self) -> None:
        assert self._history.has_no_coach_response()
        self._history.add(ChatTurn(role='user', content='hello'))
        assert self._history.has_no_coach_response()
        self._history.add(ChatTurn(role='coach', content='hello back'))
        assert not self._history.has_no_coach_response()

    def test_render(self) -> None:
        self._history.add(ChatTurn(role='user', content='Hello'))
        self._history.add(ChatTurn(role='coach', content='Hello back'))

        assert self._history.render() == 'User: Hello\nCoach: Hello back'

    def test_old_turns_are_dropped(self) -> None:
        self._history.add(ChatTurn(role='user', content='Hello'))
        self._history.add(ChatTurn(role='coach', content='Hello back'))
        self._history.add(ChatTurn(role='user', content='How are you?'))

        assert self._history.render() == 'Coach: Hello back\nUser: How are you?'
