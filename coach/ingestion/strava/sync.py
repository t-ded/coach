from collections.abc import Iterator
from typing import Any

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.mapper import map_activities
from coach.persistence.repositories.activities import SupabaseActivityRepository


def get_new_ids_only(activities: Iterator[dict[str, Any]], existing_ids: set[int]) -> Iterator[int]:
    for activity in activities:
        aid = activity['id']
        if aid not in existing_ids:
            yield aid


def sync_strava_for_user(strava_client: StravaClient, activity_repo: SupabaseActivityRepository, *, fresh: bool = False) -> int:
    if fresh:
        activity_repo.delete_all_for_user()

    cursor = activity_repo.sync_cursor()
    existing = activity_repo.existing_ids(cursor)
    recent_raw_activities = strava_client.list_activities(detailed=False, after=cursor)

    new_ids = get_new_ids_only(activities=recent_raw_activities, existing_ids=existing)
    raw_activities = (strava_client.get_detailed_activity(aid) for aid in new_ids)

    activities = map_activities(raw_activities)
    activity_repo.save_many(activities)
    return len(activities)
