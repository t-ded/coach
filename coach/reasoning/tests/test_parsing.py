import pytest

from coach.reasoning.parsing import CoachResponseParseError
from coach.reasoning.parsing import parse_coach_response


class TestParseCoachResponse:
    def test_parse_valid_tabbed_response(self) -> None:
        text = """
        Summary:
            Good progress overall.

        Observations:
                - Consistent weekly volume
        - Low intensity dominance

        Recommendations:
        - Add one tempo run
        - Maintain easy days

        Confidence Notes:
            None
        """

        result = parse_coach_response(text)

        assert result.summary == 'Good progress overall.'
        assert result.observations == ['Consistent weekly volume', 'Low intensity dominance']
        assert result.recommendations == ['Add one tempo run', 'Maintain easy days']
        assert result.confidence_notes is None

    def test_handles_multiple_header_occurrences(self) -> None:
        text = """
        Summary:
            My summary: Good progress overall.

        Observations:
                - Consistent weekly volume
        - Low intensity dominance

        Recommendations:
        - Add one tempo run
        - Maintain easy days

        Summary:
        - Some additional summary

        Confidence Notes:
            None
        """

        result = parse_coach_response(text)

        assert result.summary == 'My summary: Good progress overall.'
        assert result.observations == ['Consistent weekly volume', 'Low intensity dominance']
        assert result.recommendations == ['Add one tempo run', 'Maintain easy days']
        assert result.confidence_notes is None

    def test_missing_section_raises(self) -> None:
        with pytest.raises(CoachResponseParseError, match='Missing sections: '):
            parse_coach_response('Summary:\nOnly summary')

    def test_missing_bullets_raises(self) -> None:
        with pytest.raises(CoachResponseParseError, match='Empty section: Observations'):
            parse_coach_response(
                """
                Summary:
                Only summary

                Observations:

                Recommendations:
                - One

                Confidence Notes:
                None
                """,
            )
