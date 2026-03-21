from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.mapper import StravaMapper
from coach.persistence.repositories.activities import SupabaseActivityRepository


def sync_strava_for_user(strava_client: StravaClient, activity_repo: SupabaseActivityRepository, *, fresh: bool = False) -> int:
    if fresh:
        activity_repo.reset_table()
    mapper = StravaMapper()
    raw_activities = strava_client.list_activities(detailed=False, after=activity_repo.sync_cursor())
    activities = mapper.map_activities(raw_activities)
    activity_repo.save_many(activities)
    return len(activities)
