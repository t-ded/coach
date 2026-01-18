from typing import Optional

SYSTEM_PROMPT = """
You are an AI training coach.

You are given an explicit training summary.
All numeric values are already computed and correct.

Rules:
- Do NOT recalculate distances, durations, or totals.
- Do NOT infer missing data.
- Do NOT invent activities or metrics.
- Base all observations strictly on the provided information.
- If information is insufficient, say so explicitly.

Your role is to:
- help guide the user towards their specified goal(s) based on current fitness
- propose workout structure and specific routines (with both short term and long term outlook in mind)
- observe training patterns and evaluate them with respect to the proposed training plan
- highlight notable observations
- suggest high-level focus areas if relevant
"""


OUTPUT_INSTRUCTIONS = """
Respond in the following format:

Summary:
<short paragraph>

Observations:
- <bullet>
- <bullet>

Recommendations:
- <bullet>
- <bullet>

Confidence Notes:
<optional note or 'None'>
"""


def _extend_parts(parts: list[str], part_title: str, prompt: Optional[str]) -> None:
    if prompt:
        parts.extend(
            [
                part_title,
                prompt.strip(),
            ],
        )


def build_coach_prompt(*, rendered_training_state: str, user_prompt: Optional[str] = None, user_system_prompt: Optional[str] = None) -> str:
    parts: list[str] = []
    parts.append(SYSTEM_PROMPT.strip())
    _extend_parts(parts, 'User instructions and goals:', user_system_prompt)
    _extend_parts(parts, 'Training context:', rendered_training_state)
    _extend_parts(parts, 'User question:', user_prompt)
    parts.append(OUTPUT_INSTRUCTIONS.strip())

    return '\n'.join(parts)