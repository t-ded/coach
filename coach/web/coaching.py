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
MODE_COACH = 'coach'
MODE_PROFILE = 'profile'

_NUM_HISTORY_WEEKS = 8


def init_coach_session(profile: Optional[UserProfile], activities: list[Activity], display_name: str) -> None:
    coach = Coach(provider=LLMProvider.GOOGLE, model=None, profile=profile, activities=activities, num_history_weeks=_NUM_HISTORY_WEEKS, user_display_name=display_name)
    cl.user_session.set(SESSION_COACH, coach)
    cl.user_session.set(SESSION_MODE, MODE_COACH)


def load_coaching_data(user_id: str, authenticated_client: Client) -> tuple[Optional[UserProfile], list[Activity]]:
    strava_client = StravaClient(user_id, SupabaseStravaTokenRepository(create_secret_client()))
    activity_repo = SupabaseActivityRepository(authenticated_client, user_id)
    profile_repo = SupabaseUserProfileRepository(authenticated_client, user_id)

    sync_strava_for_user(strava_client, activity_repo)
    profile = profile_repo.load()
    activities = activity_repo.list_all()

    return profile, activities


def get_display_name(users_repo: SupabaseUsersRepository, user_identifier: str) -> str:
    display_name = users_repo.get_display_name()
    return display_name.split()[0] if display_name else user_identifier.split('@')[0]
