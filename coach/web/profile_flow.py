import re
from typing import Optional

import chainlit as cl

from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.profile_assistant.profile import apply_section_text
from coach.reasoning.profile_assistant.profile import collected_from_profile
from coach.reasoning.profile_assistant.system_prompts import SECTION_INTROS
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.web import coaching
from coach.web import session

_SESSION_PROFILE_ASSISTANT = 'profile_assistant'
_SESSION_COLLECTED_SECTIONS = 'collected_sections'
_SESSION_CURRENT_SECTION = 'current_section'
_SESSION_SECTIONS_QUEUE = 'sections_queue'
_SESSION_IS_SETUP_MODE = 'is_setup_mode'


def is_done(response: str) -> bool:
    return bool(re.search(r'(?i)\bDONE[.!]?\s*$', response.strip()))


def strip_done(response: str) -> str:
    return re.sub(r'(?i)\bDONE[.!]?\s*$', '', response).strip()


def setup_progress_message(section: ProfileParts, position: int, total: int) -> str:
    return f'Section {position} of {total}: {section.title()}'


def prompt_profile_setup(display_name: str) -> cl.Message:
    actions = [
        cl.Action(name='start_profile_setup', payload={}, label='Set up profile'),
        cl.Action(name='skip_to_coaching', payload={}, label='Skip — go straight to coaching'),
    ]
    return cl.Message(
        f"Welcome, {display_name}! Before we start, let's set up your profile so I can give you tailored guidance. "
        'This involves 5 short sections (chat preferences, training, background, constraints, and goals). '
        'You can skip any section.',
        actions=actions,
    )


async def handle_profile_message(user_input: str) -> None:
    profile_assistant: ProfileAssistant = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    response = profile_assistant.get_response(user_input)

    if is_done(response):
        visible = strip_done(response)
        if visible:
            await cl.Message(visible).send()
        await _complete_current_section()
    else:
        await cl.Message(response).send()


def _save_profile(profile: UserProfile) -> None:
    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    profile_repo = SupabaseUserProfileRepository(authenticated_client, user_id)
    profile_repo.save(profile)


async def _complete_current_section() -> None:
    profile_assistant: ProfileAssistant = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    current_section: ProfileParts = cl.user_session.get(_SESSION_CURRENT_SECTION)
    collected: dict[ProfileParts, Optional[str]] = cl.user_session.get(_SESSION_COLLECTED_SECTIONS)

    section_text = profile_assistant.summarize()
    collected[current_section] = section_text
    cl.user_session.set(_SESSION_COLLECTED_SECTIONS, collected)

    current_profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
    updated_profile = apply_section_text(current_profile, current_section, section_text)
    cl.user_session.set(coaching.SESSION_CURRENT_PROFILE, updated_profile)

    _save_profile(updated_profile)

    await cl.Message(f'✓ {current_section.title()} saved.').send()
    await _advance_profile_flow(updated_profile, 'Profile updated — coach restarted with your latest profile.')


async def handle_start_profile_setup() -> None:
    sections_queue = list(ProfileParts)
    provider, api_key = coaching.get_llm_config()
    profile_assistant = ProfileAssistant(provider=provider, model=None, api_key=api_key)
    collected: dict[ProfileParts, Optional[str]] = {}

    cl.user_session.set(_SESSION_PROFILE_ASSISTANT, profile_assistant)
    cl.user_session.set(_SESSION_COLLECTED_SECTIONS, collected)
    cl.user_session.set(_SESSION_SECTIONS_QUEUE, sections_queue)
    cl.user_session.set(_SESSION_IS_SETUP_MODE, True)

    await _enter_next_section()


async def handle_skip_to_coaching() -> None:
    activities: list[Activity] = cl.user_session.get(coaching.SESSION_ACTIVITIES)
    display_name: str = cl.user_session.get(coaching.SESSION_DISPLAY_NAME)
    coaching.init_coach_session(None, activities, display_name)
    await cl.Message('No problem! Coach is ready. What would you like to work on today?').send()


async def handle_skip_section() -> None:
    current_section: ProfileParts = cl.user_session.get(_SESSION_CURRENT_SECTION)
    collected: dict[ProfileParts, Optional[str]] = cl.user_session.get(_SESSION_COLLECTED_SECTIONS)
    collected[current_section] = None
    cl.user_session.set(_SESSION_COLLECTED_SECTIONS, collected)

    await cl.Message(f'Skipped {current_section.title()}.').send()

    profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
    await _advance_profile_flow(profile, 'Returned to coaching.')


async def handle_edit_profile() -> None:
    section_actions = [cl.Action(name='edit_section', payload={'section': section.value}, label=section.title()) for section in ProfileParts]
    await cl.Message('Which section would you like to edit?', actions=section_actions).send()


async def handle_edit_section(section: ProfileParts) -> None:
    current_profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)

    profile_assistant: Optional[ProfileAssistant] = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    if profile_assistant is None:
        provider, api_key = coaching.get_llm_config()
        profile_assistant = ProfileAssistant(provider=provider, model=None, api_key=api_key)
        cl.user_session.set(_SESSION_PROFILE_ASSISTANT, profile_assistant)

    collected = collected_from_profile(current_profile) if current_profile else {}
    cl.user_session.set(_SESSION_COLLECTED_SECTIONS, collected)
    cl.user_session.set(_SESSION_SECTIONS_QUEUE, [])
    cl.user_session.set(_SESSION_CURRENT_SECTION, section)
    cl.user_session.set(coaching.SESSION_MODE, coaching.MODE_PROFILE)

    profile_assistant.start_section(section, collected)
    existing_text = collected.get(section)

    if existing_text:
        await cl.Message(
            f'**Your current {section.title()}:**\n\n{existing_text}\n\nWhat would you like to change? '
            'Type below, or use the buttons to keep or discard this section.',
            actions=[
                cl.Action(name='keep_section', payload={}, label='Keep as is'),
                cl.Action(name='discard_section', payload={}, label='Discard section'),
            ],
        ).send()
    else:
        await cl.Message(SECTION_INTROS[section], actions=[cl.Action(name='skip_section', payload={}, label='Skip this section')]).send()


async def handle_keep_section() -> None:
    current_profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
    current_section: ProfileParts = cl.user_session.get(_SESSION_CURRENT_SECTION)
    await cl.Message(f'{current_section.title()} kept as is.').send()
    await _advance_profile_flow(current_profile, 'No changes made — coach still running with your current profile.')


async def handle_discard_section() -> None:
    current_section: ProfileParts = cl.user_session.get(_SESSION_CURRENT_SECTION)
    current_profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)

    discarded_profile = apply_section_text(current_profile, current_section, None)
    cl.user_session.set(coaching.SESSION_CURRENT_PROFILE, discarded_profile)

    _save_profile(discarded_profile)

    await cl.Message(f'✓ {current_section.title()} discarded.').send()
    await _advance_profile_flow(discarded_profile, 'Section discarded — coach restarted with your updated profile.')


async def _enter_next_section() -> None:
    sections_queue: list[ProfileParts] = cl.user_session.get(_SESSION_SECTIONS_QUEUE)
    section = sections_queue.pop(0)
    cl.user_session.set(_SESSION_SECTIONS_QUEUE, sections_queue)
    cl.user_session.set(_SESSION_CURRENT_SECTION, section)

    profile_assistant: ProfileAssistant = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    collected: dict[ProfileParts, Optional[str]] = cl.user_session.get(_SESSION_COLLECTED_SECTIONS)
    intro = profile_assistant.start_section(section, collected)

    total = len(ProfileParts)
    position = total - len(sections_queue)
    progress = setup_progress_message(section, position, total)

    actions = [cl.Action(name='skip_section', payload={}, label='Skip this section')]
    cl.user_session.set(coaching.SESSION_MODE, coaching.MODE_PROFILE)
    await cl.Message(f'{progress}\n\n{intro}', actions=actions).send()


async def _advance_profile_flow(profile: Optional[UserProfile], done_message: str) -> None:
    sections_queue: list[ProfileParts] = cl.user_session.get(_SESSION_SECTIONS_QUEUE, default=[])
    if sections_queue:
        await _enter_next_section()
        return

    activities: list[Activity] = cl.user_session.get(coaching.SESSION_ACTIVITIES)
    display_name: str = cl.user_session.get(coaching.SESSION_DISPLAY_NAME)
    coaching.init_coach_session(profile, activities, display_name)

    is_setup: bool = cl.user_session.get(_SESSION_IS_SETUP_MODE, default=False)
    if is_setup:
        cl.user_session.set(_SESSION_IS_SETUP_MODE, False)
        await cl.Message('Profile setup complete! Coach is ready. What would you like to work on today?').send()
    else:
        edit_action = cl.Action(name='edit_profile', payload={}, label='Edit Profile')
        await cl.Message(done_message, actions=[edit_action]).send()
