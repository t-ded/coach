from datetime import UTC
from datetime import datetime
from typing import Optional

import chainlit as cl
from supabase import Client

from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.sync import sync_strava_for_user
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.profiles import SupabaseUserProfileRepository
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.reasoning.coach.coach import Coach
from coach.reasoning.providers import LLMProvider

# Shared session keys — imported by profile_flow and chainlit_app
SESSION_COACH = 'coach'
SESSION_MODE = 'mode'
SESSION_ACTIVITIES = 'activities'
SESSION_DISPLAY_NAME = 'display_name'
SESSION_CURRENT_PROFILE = 'current_profile'
SESSION_LLM_PROVIDER = 'llm_provider'
SESSION_LLM_API_KEY = 'llm_api_key'
MODE_COACH = 'coach'
MODE_PROFILE = 'profile'

NUM_HISTORY_WEEKS = 8
_SYNC_COOLDOWN_SECONDS = 60 * 60  # 1 hour — suppresses idle WS reconnects; use on_chat_resume (Phase 6) to remove this


def get_llm_config() -> tuple[LLMProvider, str]:
    provider: LLMProvider = cl.user_session.get(SESSION_LLM_PROVIDER, default=LLMProvider.GOOGLE)
    api_key: str = cl.user_session.get(SESSION_LLM_API_KEY, default='')
    return provider, api_key


def init_coach_session(
    profile: Optional[UserProfile],
    activities: list[Activity],
    display_name: str,
    session_summary: Optional[str] = None,
) -> None:
    provider, api_key = get_llm_config()
    coach = Coach(
        provider=provider,
        model=None,
        api_key=api_key,
        profile=profile,
        activities=activities,
        num_history_weeks=NUM_HISTORY_WEEKS,
        user_display_name=display_name,
        session_summary=session_summary,
    )
    cl.user_session.set(SESSION_COACH, coach)
    cl.user_session.set(SESSION_MODE, MODE_COACH)


def needs_strava_sync(users_repo: SupabaseUsersRepository) -> bool:
    last = users_repo.get_last_strava_sync()
    if last is None:
        return True
    return (datetime.now(tz=UTC) - last).total_seconds() >= _SYNC_COOLDOWN_SECONDS


def load_coaching_data(
    user_id: str,
    authenticated_client: Client,
    *,
    sync_strava: bool = True,
) -> tuple[Optional[UserProfile], list[Activity]]:
    activity_repo = SupabaseActivityRepository(authenticated_client, user_id)
    profile_repo = SupabaseUserProfileRepository(authenticated_client, user_id)

    if sync_strava:
        strava_client = StravaClient(user_id, SupabaseStravaTokenRepository(create_secret_client()))
        users_repo = SupabaseUsersRepository(authenticated_client, user_id)
        sync_strava_for_user(strava_client, activity_repo)
        users_repo.set_last_strava_sync(datetime.now(tz=UTC))

    profile = profile_repo.load()
    activities = activity_repo.list_all()

    return profile, activities


def reinit_coach_from_session(session_summary: Optional[str] = None) -> None:
    profile = cl.user_session.get(SESSION_CURRENT_PROFILE)
    activities = cl.user_session.get(SESSION_ACTIVITIES)
    display_name = cl.user_session.get(SESSION_DISPLAY_NAME)
    init_coach_session(profile, activities, display_name, session_summary=session_summary)


def format_display_name(raw_display_name: Optional[str], user_identifier: str) -> str:
    return raw_display_name.split()[0] if raw_display_name else user_identifier.split('@')[0]
