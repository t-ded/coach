from typing import Optional

import chainlit as cl

from coach.auth.llm_keys import SupabaseLLMKeyRepository
from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.reasoning.providers import LLMProvider
from coach.web import coaching
from coach.web import session

_PROVIDER_DISPLAY_NAMES: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: 'Google AI Studio',
    LLMProvider.OPENAI: 'OpenAI',
}


def _display(provider: LLMProvider) -> str:
    return _PROVIDER_DISPLAY_NAMES.get(provider, provider.value.title())


def api_key_onboarding_message() -> cl.Message:
    text = (
        'To start coaching, you need to connect an AI provider API key. '
        'Only **one key** is needed — Google AI Studio is the easiest option and has a free tier.\n\n'
        '**Option A — Google AI Studio (recommended, free)**\n'
        '1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)\n'
        '2. Sign in with your Google account\n'
        '3. Click "Create API key" and copy it\n'
        '4. Click **Connect Google AI Studio** below, paste the key, then start a new chat\n\n'
        '**Option B — OpenAI**\n'
        '1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n'
        '2. Create a new secret key and copy it\n'
        '3. Click **Connect OpenAI** below, paste the key, then start a new chat'
    )
    actions = [
        cl.Action(name='set_api_key_google', payload={}, label='Connect Google AI Studio'),
        cl.Action(name='set_api_key_openai', payload={}, label='Connect OpenAI'),
    ]
    return cl.Message(text, actions=actions)


def _build_management_text(preferred: LLMProvider, stored: list[LLMProvider]) -> str:
    if not stored:
        return '**AI Provider Settings**\n\nNo API keys are stored.'
    provider_lines = '\n'.join(f'• {_display(p)}' + (' *(preferred)*' if p == preferred else '') for p in stored)
    return f'**AI Provider Settings**\n\nCurrent preferred provider: **{_display(preferred)}**\n\n**Stored keys:**\n{provider_lines}'


def _build_management_actions(preferred: LLMProvider, stored: list[LLMProvider]) -> list[cl.Action]:
    actions: list[cl.Action] = []
    non_stored = [p for p in LLMProvider if p not in stored]
    for p in non_stored:
        actions.append(cl.Action(name='add_provider_key', payload={'provider': p.value}, label=f'Add {_display(p)} key'))
    for p in stored:
        if p != preferred:
            actions.append(cl.Action(name='set_preferred_provider', payload={'provider': p.value}, label=f'Use {_display(p)}'))
        actions.append(cl.Action(name='remove_provider_key', payload={'provider': p.value}, label=f'Remove {_display(p)} key'))
    return actions


async def handle_provider_management() -> None:
    user_id = session.get_user_id()
    authenticated_client = session.get_authenticated_client()
    secret_client = create_secret_client()

    key_repo = SupabaseLLMKeyRepository(secret_client)
    stored = key_repo.list_providers(user_id)
    preferred = SupabaseUserProfileRepository(authenticated_client, user_id).get_preferred_provider()

    text = _build_management_text(preferred, stored)
    actions = _build_management_actions(preferred, stored)
    await cl.Message(text, actions=actions).send()


async def handle_set_preferred(provider: LLMProvider) -> None:
    user_id = session.get_user_id()
    authenticated_client = session.get_authenticated_client()
    secret_client = create_secret_client()

    api_key = SupabaseLLMKeyRepository(secret_client).get_key(user_id, provider)
    if api_key is None:
        await cl.Message(f'No {_display(provider)} key found. Add one first.').send()
        return

    SupabaseUserProfileRepository(authenticated_client, user_id).set_preferred_provider(provider)
    cl.user_session.set(coaching.SESSION_LLM_PROVIDER, provider)
    cl.user_session.set(coaching.SESSION_LLM_API_KEY, api_key)

    profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
    activities: list[Activity] = cl.user_session.get(coaching.SESSION_ACTIVITIES)
    display_name: str = cl.user_session.get(coaching.SESSION_DISPLAY_NAME)
    coaching.init_coach_session(profile, activities, display_name)

    actions = _ready_actions()
    await cl.Message(f'Switched to **{_display(provider)}**. Coach is ready.', actions=actions).send()


async def handle_remove_key(provider: LLMProvider) -> None:
    user_id = session.get_user_id()
    authenticated_client = session.get_authenticated_client()
    secret_client = create_secret_client()

    key_repo = SupabaseLLMKeyRepository(secret_client)
    current_preferred = SupabaseUserProfileRepository(authenticated_client, user_id).get_preferred_provider()

    key_repo.delete_key(user_id, provider)
    remaining = key_repo.list_providers(user_id)

    if not remaining:
        await api_key_onboarding_message().send()
        return

    if provider == current_preferred:
        fallback = remaining[0]
        fallback_key = key_repo.get_key(user_id, fallback)
        SupabaseUserProfileRepository(authenticated_client, user_id).set_preferred_provider(fallback)
        cl.user_session.set(coaching.SESSION_LLM_PROVIDER, fallback)
        cl.user_session.set(coaching.SESSION_LLM_API_KEY, fallback_key)

        profile: Optional[UserProfile] = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
        activities: list[Activity] = cl.user_session.get(coaching.SESSION_ACTIVITIES)
        display_name: str = cl.user_session.get(coaching.SESSION_DISPLAY_NAME)
        coaching.init_coach_session(profile, activities, display_name)

        notice = f'{_display(provider)} key removed. Now using your **{_display(fallback)}** key instead.'
        await cl.Message(notice, actions=_ready_actions()).send()
    else:
        await cl.Message(f'{_display(provider)} key removed.', actions=_ready_actions()).send()


def _help_text() -> str:
    return (
        '**How to set up an API key**\n\n'
        '**Google AI Studio (free)**\n'
        '1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)\n'
        '2. Sign in with your Google account\n'
        '3. Click "Create API key" and copy it\n'
        '4. Click **Manage AI Provider** below, then **Add Google AI Studio key**, and paste the key\n\n'
        '**OpenAI**\n'
        '1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n'
        '2. Create a new secret key and copy it\n'
        '3. Click **Manage AI Provider** below, then **Add OpenAI key**, and paste the key\n\n'
        'For more details, see the [README](https://github.com/tded/coach#api-key-setup).'
    )


async def handle_help() -> None:
    await cl.Message(_help_text(), actions=_ready_actions()).send()


def _ready_actions() -> list[cl.Action]:
    return [
        cl.Action(name='edit_profile', payload={}, label='Edit Profile'),
        cl.Action(name='manage_ai_provider', payload={}, label='Manage AI Provider'),
        cl.Action(name='help', payload={}, label='Help'),
    ]
