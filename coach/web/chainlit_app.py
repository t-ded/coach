from typing import Optional

import chainlit as cl
from starlette.routing import Mount

from coach.auth.llm_keys import LLMKeyRepository
from coach.auth.llm_keys import SupabaseLLMKeyRepository
from coach.persistence.database import create_anon_client
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.reasoning.coach.coach import Coach
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider
from coach.web import api_key_flow
from coach.web import coaching
from coach.web import profile_flow
from coach.web import session
from coach.web.api_key_routes import generate_api_key_form_url
from coach.web.app import create_app
from coach.web.auth import sign_in_with_supabase
from coach.web.google_oauth import install_patched_google_provider
from coach.web.strava_oauth import generate_strava_auth_url

install_patched_google_provider()

_PROVIDER_DISPLAY_NAMES: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: 'Google AI Studio',
    LLMProvider.OPENAI: 'OpenAI',
}

# Insert before Chainlit's routes so the SPA catch-all doesn't intercept it
_fastapi_app = create_app()
cl.server.app.router.routes.insert(0, Mount('/oauth', app=_fastapi_app))


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
    id_token: Optional[str] = None,  # never passed by Chainlit; we read from raw_user_data instead
) -> Optional[cl.User]:
    if provider_id != 'google':
        return None

    id_token = raw_user_data.get('id_token')  # noqa: S105
    if id_token is None:
        return None

    anon_client = create_anon_client()
    access_token, refresh_token, user_id, expires_at = sign_in_with_supabase(id_token, anon_client)

    default_user.metadata[session.SESSION_ACCESS_TOKEN] = access_token
    default_user.metadata[session.SESSION_REFRESH_TOKEN] = refresh_token
    default_user.metadata[session.SESSION_USER_ID] = user_id
    default_user.metadata[session.SESSION_EXPIRES_AT] = expires_at.isoformat()

    return default_user


@cl.on_chat_start
async def on_chat_start() -> None:
    user: Optional[cl.User] = cl.user_session.get('user')
    if user is None:
        await cl.Message('Authentication error — please refresh and log in again.').send()
        return

    session.init_user_session(user)

    user_id = session.get_user_id()
    authenticated_client = session.get_authenticated_client()

    # TODO (Phase 6): when persisting chat messages, exclude /oauth/api-key* routes from the thread
    secret_client = create_secret_client()
    key_repo = SupabaseLLMKeyRepository(secret_client)
    preferred_provider = SupabaseUserProfileRepository(authenticated_client, user_id).get_preferred_provider()
    api_key, active_provider, provider_notice = _resolve_llm_key(key_repo, user_id, preferred_provider)

    if api_key is None:
        await api_key_flow.api_key_onboarding_message().send()
        return

    cl.user_session.set(coaching.SESSION_LLM_PROVIDER, active_provider)
    cl.user_session.set(coaching.SESSION_LLM_API_KEY, api_key)

    users_repo = SupabaseUsersRepository(authenticated_client, user_id)
    if not users_repo.get_strava_user_id():
        await _connect_strava_prompt().send()
        return

    display_name = coaching.get_display_name(users_repo, user.identifier)
    if coaching.needs_strava_sync(user_id):
        await cl.Message('Syncing your Strava training data, please wait...').send()
    profile, activities = await cl.make_async(coaching.load_coaching_data)(user_id, authenticated_client)

    cl.user_session.set(coaching.SESSION_ACTIVITIES, activities)
    cl.user_session.set(coaching.SESSION_DISPLAY_NAME, display_name)
    cl.user_session.set(coaching.SESSION_CURRENT_PROFILE, profile)

    if profile is None:
        await profile_flow.prompt_profile_setup(display_name).send()
        return

    coaching.init_coach_session(profile, activities, display_name)
    actions = [
        cl.Action(name='edit_profile', payload={}, label='Edit Profile'),
        cl.Action(name='manage_ai_provider', payload={}, label='Manage AI Provider'),
    ]
    welcome = f'Hello, {display_name}. Coach is ready. What would you like to work on today?'
    if provider_notice:
        welcome = f'{provider_notice}\n\n{welcome}'
    await cl.Message(welcome, actions=actions).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    _ = session.get_authenticated_client()  # side-effect: refresh JWT in session if near expiry
    mode = cl.user_session.get(coaching.SESSION_MODE)

    if mode == coaching.MODE_PROFILE:
        await profile_flow.handle_profile_message(message.content)
    else:
        coach: Optional[Coach] = cl.user_session.get(coaching.SESSION_COACH)
        if coach is None:
            await cl.Message('Coach is not initialised — please refresh and reconnect Strava.').send()
            return
        reply = coach.get_response(message.content)
        await cl.Message(reply).send()


@cl.action_callback('start_profile_setup')
async def on_start_profile_setup(action: cl.Action) -> None:
    await profile_flow.handle_start_profile_setup()


@cl.action_callback('skip_to_coaching')
async def on_skip_to_coaching(action: cl.Action) -> None:
    await profile_flow.handle_skip_to_coaching()


@cl.action_callback('skip_section')
async def on_skip_section(action: cl.Action) -> None:
    await profile_flow.handle_skip_section()


@cl.action_callback('edit_profile')
async def on_edit_profile(action: cl.Action) -> None:
    await profile_flow.handle_edit_profile()


@cl.action_callback('edit_section')
async def on_edit_section(action: cl.Action) -> None:
    section = ProfileParts(action.payload['section'])
    await profile_flow.handle_edit_section(section)


@cl.action_callback('keep_section')
async def on_keep_section(action: cl.Action) -> None:
    await profile_flow.handle_keep_section()


@cl.action_callback('discard_section')
async def on_discard_section(action: cl.Action) -> None:
    await profile_flow.handle_discard_section()


@cl.action_callback('connect_strava')
async def on_connect_strava(action: cl.Action) -> None:
    user_id = session.get_user_id()
    url = generate_strava_auth_url(user_id, create_secret_client())
    await cl.Message(f'[Click here to connect Strava]({url})').send()


@cl.action_callback('set_api_key_google')
async def on_set_api_key_google(action: cl.Action) -> None:
    user_id = session.get_user_id()
    url = generate_api_key_form_url(user_id, create_secret_client(), provider='google')
    await cl.Message(f'[Click here to enter your Google AI Studio key]({url})').send()


@cl.action_callback('set_api_key_openai')
async def on_set_api_key_openai(action: cl.Action) -> None:
    user_id = session.get_user_id()
    url = generate_api_key_form_url(user_id, create_secret_client(), provider='openai')
    await cl.Message(f'[Click here to enter your OpenAI key]({url})').send()


@cl.action_callback('manage_ai_provider')
async def on_manage_ai_provider(action: cl.Action) -> None:
    await api_key_flow.handle_provider_management()


@cl.action_callback('set_preferred_provider')
async def on_set_preferred_provider(action: cl.Action) -> None:
    provider = LLMProvider(action.payload['provider'])
    await api_key_flow.handle_set_preferred(provider)


@cl.action_callback('remove_provider_key')
async def on_remove_provider_key(action: cl.Action) -> None:
    provider = LLMProvider(action.payload['provider'])
    await api_key_flow.handle_remove_key(provider)


@cl.action_callback('add_provider_key')
async def on_add_provider_key(action: cl.Action) -> None:
    provider_str: str = action.payload.get('provider', 'google')
    user_id = session.get_user_id()
    url = generate_api_key_form_url(user_id, create_secret_client(), provider=provider_str)
    provider_name = _PROVIDER_DISPLAY_NAMES.get(LLMProvider(provider_str), provider_str.title())
    await cl.Message(f'[Click here to add your {provider_name} key]({url})').send()


def _resolve_llm_key(key_repo: LLMKeyRepository, user_id: str, preferred: LLMProvider) -> tuple[Optional[str], LLMProvider, Optional[str]]:
    key = key_repo.get_key(user_id, preferred)
    if key is not None:
        return key, preferred, None
    for fallback in LLMProvider:
        if fallback != preferred:
            key = key_repo.get_key(user_id, fallback)
            if key is not None:
                notice = f'Note: using your {_PROVIDER_DISPLAY_NAMES[fallback]} key — your {_PROVIDER_DISPLAY_NAMES[preferred]} key is not configured yet.'
                return key, fallback, notice
    return None, preferred, None


def _connect_strava_prompt() -> cl.Message:
    actions = [cl.Action(name='connect_strava', payload={}, label='Connect Strava')]
    return cl.Message('To get started, please connect your Strava account.', actions=actions)
