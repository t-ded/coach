from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

from coach.domain.chat import Role
from coach.domain.session import Message
from coach.reasoning.providers import LLMProvider
from coach.reasoning.summarizer import SessionSummarizer


def _make_message(role: Role, content: str) -> Message:
    return Message(id='msg-1', session_id='sess-1', role=role, content=content, created_at=datetime.now(tz=UTC))


def test_generate_calls_llm_with_conversation() -> None:
    messages = [
        _make_message('user', 'How should I train for a 10K?'),
        _make_message('assistant', 'Start with 3 runs per week.'),
    ]

    with patch('coach.reasoning.summarizer.create_llm_client') as mock_create:
        mock_client = MagicMock()
        mock_client.complete.return_value = 'Discussed 10K training plan.'
        mock_create.return_value = mock_client

        summarizer = SessionSummarizer(provider=LLMProvider.GOOGLE, api_key='test-key')
        result = summarizer.generate(messages)

    assert result == 'Discussed 10K training plan.'
    prompt = mock_client.complete.call_args[0][0]
    assert 'How should I train for a 10K?' in prompt
    assert 'Start with 3 runs per week.' in prompt


def test_generate_formats_roles_correctly() -> None:
    messages = [
        _make_message('user', 'First question'),
        _make_message('assistant', 'First answer'),
        _make_message('user', 'Second question'),
    ]

    with patch('coach.reasoning.summarizer.create_llm_client') as mock_create:
        mock_client = MagicMock()
        mock_client.complete.return_value = 'Summary text'
        mock_create.return_value = mock_client

        summarizer = SessionSummarizer(provider=LLMProvider.GOOGLE, api_key='test-key')
        summarizer.generate(messages)

    prompt = mock_client.complete.call_args[0][0]
    assert 'User: First question' in prompt
    assert 'Assistant: First answer' in prompt
    assert 'User: Second question' in prompt
