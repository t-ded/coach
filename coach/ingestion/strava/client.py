from collections.abc import Iterator
from typing import Any

import requests

from coach.ingestion.strava.auth import StravaAuth


class StravaClient:
    def __init__(self) -> None:
        self._auth = StravaAuth()
        self._base_url = 'https://www.strava.com/api/v3'

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._auth.get_access_token()}',
        }

    def list_activities(
        self,
        *,
        per_page: int = 50,
    ) -> Iterator[dict[str, Any]]:
        page = 1

        while True:
            response = requests.get(
                f'{self._base_url}/athlete/activities',
                headers=self._headers(),
                params={
                    'page': page,
                    'per_page': per_page,
                },
                timeout=10,
            )
            response.raise_for_status()

            activities: list[dict[str, Any]] = response.json()

            if not activities:
                break

            yield from activities
            page += 1
