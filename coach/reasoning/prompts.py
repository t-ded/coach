from dataclasses import fields
from pathlib import Path
from typing import Optional

from coach.domain.models import CoachResponse
from coach.utils import parse_file

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


def _extend_parts(parts: list[str], part_title: str, prompt: Optional[str]) -> None:
    if prompt:
        parts.extend(
            [
                part_title,
                prompt.strip(),
            ],
        )


def generate_output_instructions() -> str:
    lines = ['\nRespond in the following format:\n']

    for f in fields(CoachResponse):
        header = f'{f.name.replace('_', ' ').title()}:'
        lines.append(header)
        if f.metadata.get('bullets', False):
            lines.append('- <bullet>')
            lines.append('- <bullet>')
        elif f.metadata.get('optional', False):
            lines.append("<optional content or 'None'>")
        else:
            lines.append('<content>')
        lines.append('')

    return '\n'.join(lines).strip()


def build_coach_prompt(*, rendered_training_state: str, user_prompt: Optional[str] = None, user_system_prompt_path: Path = Path('../config/coach.md')) -> str:
    parts: list[str] = []
    parts.append(SYSTEM_PROMPT.strip())
    _extend_parts(parts, 'User instructions and goals:', parse_file(user_system_prompt_path))
    _extend_parts(parts, 'Training context:', rendered_training_state)
    _extend_parts(parts, 'User question:', user_prompt)
    parts.append(generate_output_instructions().strip())

    return '\n'.join(parts)
