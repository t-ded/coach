from coach.config.logging import configure_logging
from coach.config.settings import load_strava_settings

configure_logging()


if __name__ == "__main__":
    load_strava_settings()
    pass
