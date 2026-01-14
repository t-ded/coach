from coach.config.logging import configure_logging
from coach.config.settings import load_strava_settings

configure_logging()


if __name__ == "__main__":
    load_strava_settings()
    from coach.ingestion.strava.client import StravaClient

    client = StravaClient()

    for i, activity in enumerate(client.list_activities()):
        print(activity["id"], activity["type"], activity["start_date"])
        if i >= 4:
            break
    pass
