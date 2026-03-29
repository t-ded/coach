import dataclasses
import re
from collections.abc import Mapping
from typing import Optional

from coach.builders.utils import compute_distance_duration_pace
from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.reasoning.assistant import Assistant
from coach.reasoning.coach.sections.profile import render_training_goal
from coach.reasoning.profile_assistant.system_prompts import CONVERSATION_PROMPTS
from coach.reasoning.profile_assistant.system_prompts import EDIT_PROMPTS
from coach.reasoning.profile_assistant.system_prompts import SECTION_INTROS
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider


def _parse_block(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition(':')
        fields[key.strip().lower()] = value.strip()
    return fields


def _goal_from_fields(fields: dict[str, str]) -> Optional[TrainingGoal]:
    try:
        name = fields['name']
        sport_type = SportType(fields['sport'])
        priority = Priority(fields.get('priority', 'MEDIUM').upper())
    except (KeyError, ValueError):
        return None

    goal_date = fields.get('date', 'N/A')
    notes = fields.get('notes') or None
    distance_str = fields.get('distance', '')
    duration_str = fields.get('duration', '')

    if distance_str and duration_str:
        try:
            ddp = compute_distance_duration_pace(float(distance_str), int(duration_str), None)
            return DistanceActivityTrainingGoal(
                name=name,
                sport_type=sport_type,
                goal_date=goal_date,
                priority=priority,
                notes=notes,
                goal_distance_meters=ddp.distance_meters,
                goal_duration_seconds=int(ddp.duration_seconds),
                goal_pace=ddp.pace_str,
            )
        except ValueError:
            pass

    return TrainingGoal(name=name, sport_type=sport_type, goal_date=goal_date, priority=priority, notes=notes)


def _parse_goals(raw: Optional[str]) -> Optional[tuple[TrainingGoal, ...]]:
    if not raw:
        return None
    goals = [_goal_from_fields(_parse_block(block)) for block in re.split(r'\n\s*\n', raw.strip())]
    return tuple(goal for goal in goals if goal is not None)


def _section_text(profile: UserProfile, section: ProfileParts) -> Optional[str]:
    match section:
        case ProfileParts.CHAT_PREFERENCES:
            return profile.chat_preferences
        case ProfileParts.TRAINING_PREFERENCES:
            return profile.training_preferences
        case ProfileParts.PERSONAL_INFORMATION:
            return profile.personal_information
        case ProfileParts.CONSTRAINTS:
            return profile.constraints
        case ProfileParts.GOALS:
            return '\n'.join(render_training_goal(g) for g in profile.goals) if profile.goals else None


def _build_context_note(collected: dict[ProfileParts, Optional[str]]) -> str:
    entries = [(section, text) for section, text in collected.items() if text]
    if not entries:
        return ''
    lines = ['The following sections have ALREADY been collected in this session. Do NOT re-ask about these topics:']
    for section, text in entries:
        lines.append(f'\n[{section.title()}]\n{text}')
    return '\n'.join(lines)


def collected_from_profile(profile: UserProfile) -> dict[ProfileParts, Optional[str]]:
    return {section: _section_text(profile, section) for section in ProfileParts}


def apply_section_text(profile: Optional[UserProfile], section: ProfileParts, text: Optional[str]) -> UserProfile:
    base = profile or UserProfile()
    match section:
        case ProfileParts.CHAT_PREFERENCES:
            return dataclasses.replace(base, chat_preferences=text)
        case ProfileParts.TRAINING_PREFERENCES:
            return dataclasses.replace(base, training_preferences=text)
        case ProfileParts.PERSONAL_INFORMATION:
            return dataclasses.replace(base, personal_information=text)
        case ProfileParts.CONSTRAINTS:
            return dataclasses.replace(base, constraints=text)
        case ProfileParts.GOALS:
            return dataclasses.replace(base, goals=_parse_goals(text))


class ProfileAssistant(Assistant):
    def __init__(self, provider: LLMProvider, model: Optional[str], api_key: Optional[str] = None) -> None:
        super().__init__(provider=provider, model=model, api_key=api_key)
        self._current_section: ProfileParts = ProfileParts.CHAT_PREFERENCES
        self._collected_sections: dict[ProfileParts, Optional[str]] = {}

    @property
    def _is_editing(self) -> bool:
        return bool(self._collected_sections.get(self._current_section))

    def _system_prompt(self) -> str:
        return EDIT_PROMPTS[self._current_section] if self._is_editing else CONVERSATION_PROMPTS[self._current_section]

    def _additional_context(self) -> Optional[str]:
        other_sections = self._collected_sections.copy()
        previous = other_sections.pop(self._current_section, None)
        parts = [
            _build_context_note(other_sections),
            f'The user is editing this section. Previous value:\n{previous}' if previous else '',
        ]
        return '\n\n'.join(p for p in parts if p) or None

    def start_section(self, section: ProfileParts, collected: Mapping[ProfileParts, Optional[str]]) -> str:
        self._history.clear()
        self._current_section = section
        self._collected_sections = dict(collected)
        return SECTION_INTROS[section]

    def summarize(self) -> Optional[str]:
        if self._history.has_no_assistant_response():
            return None

        prompt = self._summarize_goals_prompt if self._current_section == ProfileParts.GOALS else self._summarize_text_prompt
        return self._llm_client.complete(prompt)

    _GOALS_OUTPUT_FORMAT = """Output one block per goal, separated by blank lines. Each block must contain exactly these labeled lines (leave the value empty if not applicable):

Name: <goal name>
Sport: <Run | Ride | Swim | Walk | WeightTraining | Other>
Date: <YYYY-MM-DD | N/A>
Priority: <LOW | MEDIUM | HIGH | VERY HIGH>
Distance: <distance in meters, or empty>
Duration: <duration in seconds, or empty>
Notes: <any additional notes, or empty>

The formatting is absolutely crucial for automatic parsing. No other text, no headings, no numbering — just the labeled blocks."""

    @property
    def _summarize_text_prompt(self) -> str:
        original = self._collected_sections.get(self._current_section)
        if original:
            return f"""Below is a conversation where a user described updates to their {self._current_section} for an AI coaching assistant.

Original {self._current_section}:
{original}

Conversation about requested changes:
{self._history.render()}

Produce an updated {self._current_section} that incorporates the requested changes while preserving all other information unchanged.

Updated {self._current_section} (bullet points only, no preamble):
"""
        return f"""
Below is a conversation where a user described their {self._current_section} for an AI coaching assistant.

Distill the key points into 3-10 concise bullet points.
The user's profile should be clearly described by this and the user should feel well known and understood when these bullet points are displayed to him/her.

Conversation:
{self._history.render()}

Summary (bullet points only, no preamble):
"""

    @property
    def _summarize_goals_prompt(self) -> str:
        original = self._collected_sections.get(self._current_section)
        if original:
            return f"""Below is a conversation where a user described updates to their training goals for an AI coaching assistant.

Current goals:
{original}

Conversation about requested changes:
{self._history.render()}

{self._GOALS_OUTPUT_FORMAT}

Apply only the changes the user requested. Include ALL goals — both changed and unchanged — in the output.
"""
        return f"""
Below is a conversation where a user described their training goals for an AI coaching assistant.

{self._GOALS_OUTPUT_FORMAT}

Conversation:
{self._history.render()}
"""
