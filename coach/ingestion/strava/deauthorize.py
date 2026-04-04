import logging

from supabase import Client

from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.users import SupabaseUsersRepository

logger = logging.getLogger(__name__)


def deauthorize_athlete(strava_athlete_id: int, secret_client: Client) -> None:
    user_id = SupabaseUsersRepository.find_user_id_by_strava_id(secret_client, strava_athlete_id)
    if user_id is None:
        logger.info('Deauthorization event for unknown Strava athlete %d — ignored.', strava_athlete_id)
        return

    SupabaseStravaTokenRepository(secret_client).delete_tokens(user_id)
    SupabaseActivityRepository(secret_client, user_id).delete_all_for_user()
    SupabaseUsersRepository(secret_client, user_id).clear_strava_user_id()

    logger.info('Deauthorized Strava athlete %d (user %s).', strava_athlete_id, user_id)
