from collections.abc import Iterator
from typing import Any

import requests

from coach.config.env import get_env_var
from coach.ingestion.strava.auth import StravaAuth


class StravaClient:
    def __init__(self) -> None:
        self._auth = StravaAuth()
        self._base_url = get_env_var('STRAVA_API_BASE_URL')

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._auth.get_access_token()}',
        }

    def list_activities(self, *, detailed: bool = True, per_page: int = 50, after: int = 0) -> Iterator[dict[str, Any]]:
        page = 1

        while True:
            response = requests.get(
                f'{self._base_url}/athlete/activities',
                headers=self._headers(),
                params={'after': after, 'page': page, 'per_page': per_page},
                timeout=10,
            )
            response.raise_for_status()

            activities: list[dict[str, Any]] = response.json()

            if not activities:
                break

            for activity in activities:
                if detailed:
                    yield self.get_detailed_activity(activity['id'])
                else:
                    yield activity

            page += 1

    def get_detailed_activity(self, activity_id: int) -> dict[str, Any]:
        response = requests.get(
            f'{self._base_url}/activities/{activity_id}',
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_athlete(self) -> dict[str, Any]:
        response = requests.get(
            f'{self._base_url}/athlete',
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_athlete_id(self) -> int:
        athlete = self.get_athlete()
        return athlete['id']

    def get_athlete_stats(self) -> dict[str, Any]:
        athlete_id = self.get_athlete_id()
        response = requests.get(
            f'{self._base_url}/athletes/{athlete_id}/stats',
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
