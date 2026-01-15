from coach.config.logging import configure_logging
from coach.config.settings import load_strava_settings
from coach.ingestion.strava.mapper import StravaMapper
from coach.ingestion.strava.client import StravaClient

configure_logging()


if __name__ == "__main__":
    load_strava_settings()

    client = StravaClient()
    mapper = StravaMapper()

    for i, activity in enumerate(client.list_activities()):
        print(activity["id"], activity["type"], activity["start_date"])
        print(mapper.map_strava_activity(activity))
        if i >= 4:
            break
    pass
