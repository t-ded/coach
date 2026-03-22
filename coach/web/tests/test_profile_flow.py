from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.web.profile_flow import is_done
from coach.web.profile_flow import setup_progress_message
from coach.web.profile_flow import strip_done


class TestIsDone:
    def test_returns_true_for_done_at_end(self) -> None:
        assert is_done('Nice work. DONE') is True

    def test_returns_true_with_punctuation(self) -> None:
        assert is_done('Great session! DONE.') is True

    def test_returns_true_case_insensitive(self) -> None:
        assert is_done('done') is True

    def test_returns_false_when_done_not_at_end(self) -> None:
        assert is_done('DONE but there is more') is False

    def test_returns_false_for_regular_message(self) -> None:
        assert is_done('Keep up the good work!') is False


class TestStripDone:
    def test_strips_done_from_end(self) -> None:
        assert strip_done('Nice work. DONE') == 'Nice work.'

    def test_strips_done_with_exclamation(self) -> None:
        assert strip_done('Great session! DONE!') == 'Great session!'

    def test_no_change_when_no_done(self) -> None:
        assert strip_done('Keep it up!') == 'Keep it up!'

    def test_strips_done_leaving_empty_string(self) -> None:
        assert strip_done('DONE') == ''


class TestSetupProgressMessage:
    def test_first_section(self) -> None:
        assert setup_progress_message(ProfileParts.CHAT_PREFERENCES, 1, 5) == 'Section 1 of 5: Chat Preferences'

    def test_middle_section(self) -> None:
        assert setup_progress_message(ProfileParts.TRAINING_PREFERENCES, 2, 5) == 'Section 2 of 5: Training Preferences'

    def test_last_section(self) -> None:
        assert setup_progress_message(ProfileParts.GOALS, 5, 5) == 'Section 5 of 5: Goals'
