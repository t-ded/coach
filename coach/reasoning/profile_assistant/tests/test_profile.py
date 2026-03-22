from unittest.mock import MagicMock
from unittest.mock import patch

from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.profile_assistant.system_prompts import SECTION_INTROS
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider


class TestProfileAssistantStartSection:
    def setup_method(self) -> None:
        with patch('coach.reasoning.assistant.create_llm_client'):
            self._assistant = ProfileAssistant(provider=LLMProvider.GOOGLE, model=None)

    def test_returns_section_intro_string(self) -> None:
        intro = self._assistant.start_section(ProfileParts.CHAT_PREFERENCES, {})
        assert intro == SECTION_INTROS[ProfileParts.CHAT_PREFERENCES]

    def test_returns_correct_intro_for_each_section(self) -> None:
        for section in ProfileParts:
            intro = self._assistant.start_section(section, {})
            assert intro == SECTION_INTROS[section]

    def test_collected_sections_appear_in_additional_context(self) -> None:
        mock_client = MagicMock()
        mock_client.complete.return_value = 'Some response'
        with patch('coach.reasoning.assistant.create_llm_client', return_value=mock_client):
            assistant = ProfileAssistant(provider=LLMProvider.GOOGLE, model=None)

        collected = {ProfileParts.CHAT_PREFERENCES: 'I prefer brief, direct responses'}
        assistant.start_section(ProfileParts.TRAINING_PREFERENCES, collected)
        assistant.get_response('I run 5 times a week')

        prompt_used = mock_client.complete.call_args[0][0]
        assert 'I prefer brief, direct responses' in prompt_used


class TestProfileAssistantSummarize:
    def setup_method(self) -> None:
        self._mock_client = MagicMock()
        self._mock_client.complete.return_value = 'Some response from LLM'
        with patch('coach.reasoning.assistant.create_llm_client', return_value=self._mock_client):
            self._assistant = ProfileAssistant(provider=LLMProvider.GOOGLE, model=None)

    def test_returns_none_with_no_history(self) -> None:
        self._assistant.start_section(ProfileParts.CHAT_PREFERENCES, {})
        assert self._assistant.summarize() is None

    def test_returns_string_after_response(self) -> None:
        self._assistant.start_section(ProfileParts.CHAT_PREFERENCES, {})
        self._assistant.get_response('I like short answers')
        result = self._assistant.summarize()
        assert result is not None

    def test_summarize_calls_llm_with_conversation_history(self) -> None:
        self._assistant.start_section(ProfileParts.CHAT_PREFERENCES, {})
        self._assistant.get_response('I like short answers')
        self._mock_client.complete.reset_mock()
        self._assistant.summarize()
        self._mock_client.complete.assert_called_once()
