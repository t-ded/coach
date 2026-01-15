from coach.config.logging import configure_logging
from coach.config.settings import load_strava_settings
from coach.ingestion.strava.mapper import StravaMapper
from coach.ingestion.strava.client import StravaClient
from coach.storage.sqlite import SQLiteActivityRepository

configure_logging()


if __name__ == "__main__":
    load_strava_settings()

    client = StravaClient()
    mapper = StravaMapper()
    repo = SQLiteActivityRepository('coach.db')

    activities = [mapper.map_strava_activity(raw_activity) for raw_activity in client.list_activities()]
    repo.save_many(activities)
