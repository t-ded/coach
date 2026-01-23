from coach.reasoning.prompts import INITIAL_OUTPUT_INSTRUCTIONS
from coach.reasoning.prompts import generate_output_instructions


def test_generate_output_instructions() -> None:
    expected_initial_output_prompt = """
Respond in the following format:

Summary:
<content>

Observations:
- <bullet>
- <bullet>

Recommendations:
- <bullet>
- <bullet>

Confidence Notes:
<optional content or 'None'>
"""
    expected_has_history_output_prompt = 'Your answer: <response>\n'

    actual_initial_output_prompt = generate_output_instructions(has_history=False)
    actual_has_history_output_prompt = generate_output_instructions(has_history=True)

    assert actual_initial_output_prompt == expected_initial_output_prompt.strip()
    assert actual_initial_output_prompt == INITIAL_OUTPUT_INSTRUCTIONS
    assert actual_has_history_output_prompt == expected_has_history_output_prompt
