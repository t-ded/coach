from coach.reasoning.prompts import generate_output_instructions


def test_generate_output_instructions() -> None:
    expected_output_prompt = """
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
    assert generate_output_instructions() == expected_output_prompt.strip()

