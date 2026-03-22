import re
from datetime import datetime
from typing import Optional

import chainlit as cl
from starlette.routing import Mount
from supabase import Client

from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.sync import sync_strava_for_user
from coach.persistence.database import create_anon_client
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.reasoning.coach.coach import Coach
from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.profile_assistant.profile import apply_section_text
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider
from coach.web.app import create_app
from coach.web.auth import build_authenticated_client
from coach.web.auth import refresh_if_needed
from coach.web.auth import sign_in_with_supabase
from coach.web.google_oauth import install_patched_google_provider
from coach.web.strava_oauth import generate_strava_auth_url

install_patched_google_provider()

_SESSION_ACCESS_TOKEN = 'supabase_access_token'  # noqa: S105
_SESSION_REFRESH_TOKEN = 'supabase_refresh_token'  # noqa: S105
_SESSION_USER_ID = 'supabase_user_id'
_SESSION_EXPIRES_AT = 'supabase_expires_at'

# Insert before Chainlit's routes so the SPA catch-all doesn't intercept it
_fastapi_app = create_app()
cl.server.app.router.routes.insert(0, Mount('/oauth', app=_fastapi_app))


_SESSION_COACH = 'coach'
_SESSION_MODE = 'mode'
_SESSION_PROFILE_ASSISTANT = 'profile_assistant'
_SESSION_COLLECTED_SECTIONS = 'collected_sections'
_SESSION_CURRENT_SECTION = 'current_section'
_SESSION_CURRENT_PROFILE = 'current_profile'
_SESSION_ACTIVITIES = 'activities'
_SESSION_DISPLAY_NAME = 'display_name'

_MODE_COACH = 'coach'
_MODE_PROFILE = 'profile'

_NUM_HISTORY_WEEKS = 8


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

    default_user.metadata[_SESSION_ACCESS_TOKEN] = access_token
    default_user.metadata[_SESSION_REFRESH_TOKEN] = refresh_token
    default_user.metadata[_SESSION_USER_ID] = user_id
    default_user.metadata[_SESSION_EXPIRES_AT] = expires_at.isoformat()

    return default_user


@cl.on_chat_start
async def on_chat_start() -> None:
    user: Optional[cl.User] = cl.user_session.get('user')
    if user is None:
        await cl.Message('Authentication error — please refresh and log in again.').send()
        return

    _init_user_session(user)

    user_id: str = cl.user_session.get(_SESSION_USER_ID)
    authenticated_client = _get_authenticated_client()
    users_repo = SupabaseUsersRepository(authenticated_client, user_id)

    if not users_repo.get_strava_user_id():
        await _connect_strava_user_prompt().send()
        return

    display_name = _get_display_name(users_repo, user.identifier)
    profile, activities = _load_coaching_data(user_id, authenticated_client)

    cl.user_session.set(_SESSION_DISPLAY_NAME, display_name)
    cl.user_session.set(_SESSION_ACTIVITIES, activities)
    cl.user_session.set(_SESSION_CURRENT_PROFILE, profile)

    _init_coach_session(profile, activities, display_name)
    await cl.Message(f'Hello, {display_name}. Coach is ready. What would you like to work on today?').send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    _ = _get_authenticated_client()  # side-effect: refresh JWT in session if near expiry
    mode = cl.user_session.get(_SESSION_MODE)

    if mode == _MODE_PROFILE:
        await _handle_profile_message(message.content)
    else:
        coach = cl.user_session.get(_SESSION_COACH)
        if coach is None:
            await cl.Message('Coach is not initialised — please refresh and reconnect Strava.').send()
            return
        reply = coach.get_response(message.content)
        await cl.Message(reply).send()


async def _handle_profile_message(user_input: str) -> None:
    profile_assistant: ProfileAssistant = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    response = profile_assistant.get_response(user_input)

    if _is_done(response):
        visible = _strip_done(response)
        if visible:
            await cl.Message(visible).send()
        await _complete_current_section()
    else:
        await cl.Message(response).send()


async def _complete_current_section() -> None:
    profile_assistant: ProfileAssistant = cl.user_session.get(_SESSION_PROFILE_ASSISTANT)
    current_section: ProfileParts = cl.user_session.get(_SESSION_CURRENT_SECTION)
    collected: dict[ProfileParts, Optional[str]] = cl.user_session.get(_SESSION_COLLECTED_SECTIONS)

    section_text = profile_assistant.summarize()
    collected[current_section] = section_text
    cl.user_session.set(_SESSION_COLLECTED_SECTIONS, collected)

    current_profile: Optional[UserProfile] = cl.user_session.get(_SESSION_CURRENT_PROFILE)
    updated_profile = apply_section_text(current_profile, current_section, section_text)
    cl.user_session.set(_SESSION_CURRENT_PROFILE, updated_profile)

    authenticated_client = _get_authenticated_client()
    user_id: str = cl.user_session.get(_SESSION_USER_ID)
    profile_repo = SupabaseUserProfileRepository(authenticated_client, user_id)
    profile_repo.save(updated_profile)

    await cl.Message(f'✓ {current_section.title()} saved.').send()

    activities: list[Activity] = cl.user_session.get(_SESSION_ACTIVITIES)
    display_name: str = cl.user_session.get(_SESSION_DISPLAY_NAME)
    _init_coach_session(updated_profile, activities, display_name)
    await cl.Message('Profile updated — coach restarted with your latest profile.').send()


def _init_coach_session(profile: Optional[UserProfile], activities: list[Activity], display_name: str) -> None:
    coach = Coach(provider=LLMProvider.GOOGLE, model=None, profile=profile, activities=activities, num_history_weeks=_NUM_HISTORY_WEEKS, user_display_name=display_name)
    cl.user_session.set(_SESSION_COACH, coach)
    cl.user_session.set(_SESSION_MODE, _MODE_COACH)


def _is_done(response: str) -> bool:
    return bool(re.search(r'(?i)\bDONE[.!]?\s*$', response.strip()))


def _strip_done(response: str) -> str:
    return re.sub(r'(?i)\bDONE[.!]?\s*$', '', response).strip()


def _connect_strava_user_prompt() -> cl.Message:
    actions = [cl.Action(name='connect_strava', payload={}, label='Connect Strava')]
    return cl.Message('To get started, please connect your Strava account.', actions=actions)


@cl.action_callback('connect_strava')
async def on_connect_strava(action: cl.Action) -> None:
    user_id: str = cl.user_session.get(_SESSION_USER_ID)
    url = generate_strava_auth_url(user_id, create_secret_client())
    await cl.Message(f'[Click here to connect Strava]({url})').send()


def _get_display_name(users_repo: SupabaseUsersRepository, user_identifier: str) -> str:
    display_name = users_repo.get_display_name()
    return display_name.split()[0] if display_name else user_identifier.split('@')[0]


def _load_coaching_data(user_id: str, authenticated_client: Client) -> tuple[Optional[UserProfile], list[Activity]]:
    strava_client = StravaClient(user_id, SupabaseStravaTokenRepository(create_secret_client()))
    activity_repo = SupabaseActivityRepository(authenticated_client, user_id)
    profile_repo = SupabaseUserProfileRepository(authenticated_client, user_id)

    sync_strava_for_user(strava_client, activity_repo)
    profile = profile_repo.load()
    activities = activity_repo.list_all()

    return profile, activities


def _init_user_session(user: cl.User) -> None:
    metadata = user.metadata
    cl.user_session.set(_SESSION_ACCESS_TOKEN, metadata[_SESSION_ACCESS_TOKEN])
    cl.user_session.set(_SESSION_REFRESH_TOKEN, metadata[_SESSION_REFRESH_TOKEN])
    cl.user_session.set(_SESSION_USER_ID, metadata[_SESSION_USER_ID])
    cl.user_session.set(_SESSION_EXPIRES_AT, datetime.fromisoformat(metadata[_SESSION_EXPIRES_AT]))


def _get_authenticated_client() -> Client:
    access_token: str = cl.user_session.get(_SESSION_ACCESS_TOKEN)
    refresh_token: str = cl.user_session.get(_SESSION_REFRESH_TOKEN)
    expires_at: datetime = cl.user_session.get(_SESSION_EXPIRES_AT)

    anon_client = create_anon_client()
    access_token, refresh_token, expires_at = refresh_if_needed(access_token, refresh_token, expires_at, anon_client)

    cl.user_session.set(_SESSION_ACCESS_TOKEN, access_token)
    cl.user_session.set(_SESSION_REFRESH_TOKEN, refresh_token)
    cl.user_session.set(_SESSION_EXPIRES_AT, expires_at)

    return build_authenticated_client(access_token, refresh_token, anon_client)
