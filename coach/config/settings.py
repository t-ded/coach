from dataclasses import dataclass

from coach.config.env import get_env_var


@dataclass(frozen=True, slots=True)
class StravaSettings:
    client_id: str
    client_secret: str
    refresh_token: str


def load_strava_settings() -> StravaSettings:
    return StravaSettings(
        client_id=get_env_var('STRAVA_CLIENT_ID'),
        client_secret=get_env_var('STRAVA_CLIENT_SECRET'),
        refresh_token=get_env_var('STRAVA_REFRESH_TOKEN'),
    )
