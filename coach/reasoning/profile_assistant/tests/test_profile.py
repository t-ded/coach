from unittest.mock import MagicMock
from unittest.mock import patch

from coach.domain.profile import UserProfile
from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.profile_assistant.profile import apply_section_text
from coach.reasoning.profile_assistant.profile import collected_from_profile
from coach.reasoning.profile_assistant.system_prompts import SECTION_INTROS
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider


class TestApplySectionText:
    def test_applies_chat_preferences(self) -> None:
        profile = apply_section_text(None, ProfileParts.CHAT_PREFERENCES, 'Be brief')
        assert profile.chat_preferences == 'Be brief'

    def test_applies_training_preferences(self) -> None:
        profile = apply_section_text(None, ProfileParts.TRAINING_PREFERENCES, 'I run 5x per week')
        assert profile.training_preferences == 'I run 5x per week'

    def test_applies_personal_information(self) -> None:
        profile = apply_section_text(None, ProfileParts.PERSONAL_INFORMATION, 'Age 30, healthy')
        assert profile.personal_information == 'Age 30, healthy'

    def test_applies_constraints(self) -> None:
        profile = apply_section_text(None, ProfileParts.CONSTRAINTS, 'No weekends')
        assert profile.constraints == 'No weekends'

    def test_applies_none_text_leaves_field_none(self) -> None:
        profile = apply_section_text(None, ProfileParts.CHAT_PREFERENCES, None)
        assert profile.chat_preferences is None

    def test_preserves_existing_sections_when_updating_one(self) -> None:
        existing = UserProfile(chat_preferences='Be brief', training_preferences='Run daily')
        updated = apply_section_text(existing, ProfileParts.TRAINING_PREFERENCES, 'Run 3x per week')
        assert updated.chat_preferences == 'Be brief'
        assert updated.training_preferences == 'Run 3x per week'

    def test_builds_from_none_profile_with_all_other_fields_none(self) -> None:
        profile = apply_section_text(None, ProfileParts.CONSTRAINTS, 'No late nights')
        assert profile.chat_preferences is None
        assert profile.training_preferences is None
        assert profile.personal_information is None
        assert profile.goals is None
        assert profile.constraints == 'No late nights'

    def test_applies_goals_text_and_parses_into_goals(self) -> None:
        goals_text = 'Name: Parkrun\nSport: Run\nDate: N/A\nPriority: MEDIUM\nDistance: \nDuration: \nNotes: '
        profile = apply_section_text(None, ProfileParts.GOALS, goals_text)
        assert profile.goals is not None
        assert len(profile.goals) == 1
        assert profile.goals[0].name == 'Parkrun'

    def test_applies_none_goals_text_leaves_goals_none(self) -> None:
        profile = apply_section_text(None, ProfileParts.GOALS, None)
        assert profile.goals is None


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


class TestCollectedFromProfile:
    def test_maps_all_sections_from_profile(self) -> None:
        profile = UserProfile(
            chat_preferences='Be brief',
            training_preferences='Run daily',
            personal_information='Age 30',
            constraints='No weekends',
            goals=None,
        )
        result = collected_from_profile(profile)
        assert result[ProfileParts.CHAT_PREFERENCES] == 'Be brief'
        assert result[ProfileParts.TRAINING_PREFERENCES] == 'Run daily'
        assert result[ProfileParts.PERSONAL_INFORMATION] == 'Age 30'
        assert result[ProfileParts.CONSTRAINTS] == 'No weekends'
        assert result[ProfileParts.GOALS] is None

    def test_none_fields_map_to_none(self) -> None:
        profile = UserProfile()
        result = collected_from_profile(profile)
        for section in ProfileParts:
            assert result[section] is None

    def test_all_profile_parts_present(self) -> None:
        profile = UserProfile()
        result = collected_from_profile(profile)
        assert set(result.keys()) == set(ProfileParts)
