import dataclasses
import re
from typing import Optional

import typer

from coach.builders.utils import compute_distance_duration_pace
from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.reasoning.assistant import Assistant
from coach.reasoning.coach.context import render_training_goal
from coach.reasoning.profile_assistant.system_prompts import CONVERSATION_PROMPTS
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
                name=name, sport_type=sport_type, goal_date=goal_date, priority=priority, notes=notes,
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


class ProfileAssistant(Assistant):
    def __init__(self, provider: LLMProvider, model: Optional[str]) -> None:
        super().__init__(provider=provider, model=model)
        self._current_section: ProfileParts = ProfileParts.CHAT_PREFERENCES
        self._collected_sections: dict[ProfileParts, Optional[str]] = {}

    def _system_prompt(self) -> str:
        return CONVERSATION_PROMPTS[self._current_section]

    def _additional_context(self) -> Optional[str]:
        other_sections = self._collected_sections.copy()
        previous = other_sections.pop(self._current_section, None)
        parts = [
            _build_context_note(other_sections),
            f'The user is editing this section. Previous value:\n{previous}' if previous else '',
        ]
        return '\n\n'.join(p for p in parts if p) or None

    def setup_profile(self) -> UserProfile:
        typer.echo("\nWelcome to Coach! Let's set up your profile so I can give you tailored guidance.\n")
        typer.echo('For each section, answer the prompt and continue the conversation. Press Enter on an empty line to move to the next section.\n')

        self._collected_sections = {}
        chat_preferences = self._collect_text(ProfileParts.CHAT_PREFERENCES)
        self._collected_sections[ProfileParts.CHAT_PREFERENCES] = chat_preferences

        training_preferences = self._collect_text(ProfileParts.TRAINING_PREFERENCES)
        self._collected_sections[ProfileParts.TRAINING_PREFERENCES] = training_preferences

        personal_information = self._collect_text(ProfileParts.PERSONAL_INFORMATION)
        self._collected_sections[ProfileParts.PERSONAL_INFORMATION] = personal_information

        constraints = self._collect_text(ProfileParts.CONSTRAINTS)
        self._collected_sections[ProfileParts.CONSTRAINTS] = constraints

        goals_text = self._collect_text(ProfileParts.GOALS)

        typer.echo('\nProfile setup complete! Coach can now provide tailored guidance.\n')
        return UserProfile(
            chat_preferences=chat_preferences,
            training_preferences=training_preferences,
            personal_information=personal_information,
            constraints=constraints,
            goals=_parse_goals(goals_text),
        )

    def edit_section(self, section: ProfileParts, profile: UserProfile) -> UserProfile:
        self._collected_sections = {part: _section_text(profile, part) for part in ProfileParts}
        new_text = self._collect_text(section)
        match section:
            case ProfileParts.CHAT_PREFERENCES:
                return dataclasses.replace(profile, chat_preferences=new_text)
            case ProfileParts.TRAINING_PREFERENCES:
                return dataclasses.replace(profile, training_preferences=new_text)
            case ProfileParts.PERSONAL_INFORMATION:
                return dataclasses.replace(profile, personal_information=new_text)
            case ProfileParts.CONSTRAINTS:
                return dataclasses.replace(profile, constraints=new_text)
            case ProfileParts.GOALS:
                return dataclasses.replace(profile, goals=_parse_goals(new_text))

    def _collect_text(self, section: ProfileParts) -> Optional[str]:
        try:
            self._run_conversation_loop(section)
            return self._summarize(section)
        except (RuntimeError, ValueError) as e:
            typer.echo(f'Error: {e} when collecting section {section.value}')
            return None

    def _run_conversation_loop(self, section: ProfileParts) -> None:
        self._history.clear()
        self._current_section = section
        typer.echo(f'\n{SECTION_INTROS[section]}\n')
        while True:
            user_input = self._read_input()
            if not user_input.strip():
                return
            typer.echo('Thank you for your input!')

            response = self._get_response(user_input)
            if response.strip().upper() == 'DONE':
                return

            typer.echo(f'\nAssistant:\n{response}\n')

    @staticmethod
    def _read_input() -> str:
        typer.echo('Your answer: ', nl=False)
        lines: list[str] = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        return '\n'.join(lines)

    def _summarize(self, section: ProfileParts) -> Optional[str]:
        if self._history.has_no_assistant_response():
            return None

        prompt = self._summarize_goals_prompt if section == ProfileParts.GOALS else self._summarize_text_prompt
        return self._llm_client.complete(prompt)

    @property
    def _summarize_text_prompt(self) -> str:
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
        return f"""
Below is a conversation where a user described their training goals for an AI coaching assistant.

Output one block per goal, separated by blank lines. Each block must contain exactly these labeled lines (leave the value empty if not applicable):

Name: <goal name>
Sport: <Run | Ride | Swim | Walk | WeightTraining | Other>
Date: <YYYY-MM-DD | N/A>
Priority: <LOW | MEDIUM | HIGH | VERY HIGH>
Distance: <distance in meters, or empty>
Duration: <duration in seconds, or empty>
Notes: <any additional notes, or empty>

The formatting is absolutely crucial, so that the response can be automatically parsed.
No other text, no headings, no numbering — just the labeled blocks.

Conversation:
{self._history.render()}
"""
