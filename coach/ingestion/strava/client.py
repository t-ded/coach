import logging
import time
from collections.abc import Iterator
from typing import Any

import requests

from coach.config.env import get_env_var
from coach.ingestion.strava.auth import StravaAuth

logger = logging.getLogger(__name__)


class StravaRateLimitError(Exception):
    pass


class StravaClient:
    # Strava enforces a 15-minute and daily rate limit.
    # We back off and retry when we hit the 15-minute limit.
    _RATE_LIMIT_STATUS = 429
    _MAX_RETRIES = 3
    _FIFTEEN_MINUTES = 15 * 60

    def __init__(self) -> None:
        self._auth = StravaAuth()
        self._base_url = get_env_var('STRAVA_API_BASE_URL')

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._auth.get_access_token()}',
        }

    def _seconds_until_next_window(self) -> int:
        now = time.time()
        return self._FIFTEEN_MINUTES - (int(now) % self._FIFTEEN_MINUTES)

    def _get(self, url: str, **kwargs: Any) -> Any:
        for attempt in range(self._MAX_RETRIES):
            response = requests.get(url, headers=self._headers(), timeout=10, **kwargs)

            if response.status_code != self._RATE_LIMIT_STATUS:
                response.raise_for_status()
                return response.json()

            usage = response.headers.get('X-RateLimit-Usage', '')
            limits = response.headers.get('X-RateLimit-Limit', '')
            fifteen_min_used, daily_used = (int(x) for x in usage.split(','))
            fifteen_min_limit, daily_limit = (int(x) for x in limits.split(','))

            if daily_used >= daily_limit:
                raise StravaRateLimitError(f'Daily rate limit reached ({daily_used}/{daily_limit}).')

            if attempt == self._MAX_RETRIES - 1:
                raise StravaRateLimitError(f'15-minute rate limit still exceeded after {self._MAX_RETRIES} attempts.')

            wait = self._seconds_until_next_window()
            logger.warning('15-minute rate limit hit. Waiting %ds until next window (attempt %d/%d).', wait, attempt + 1, self._MAX_RETRIES - 1)
            time.sleep(wait)

        raise StravaRateLimitError('Maximum number of retries exceeded.')

    def list_activities(self, *, detailed: bool = True, per_page: int = 50, after: int = 0) -> Iterator[dict[str, Any]]:
        page = 1

        while True:
            activities = self._get(
                url=f'{self._base_url}/athlete/activities',
                params={'after': after, 'page': page, 'per_page': per_page},
            )

            if not activities:
                break

            for activity in activities:
                if detailed:
                    yield self.get_detailed_activity(activity['id'])
                else:
                    yield activity

            page += 1

    def get_detailed_activity(self, activity_id: int) -> dict[str, Any]:
        return self._get(f'{self._base_url}/activities/{activity_id}')

    def get_athlete(self) -> dict[str, Any]:
        return self._get(f'{self._base_url}/athlete')

    def get_athlete_id(self) -> int:
        return self.get_athlete()['id']

    def get_athlete_stats(self) -> dict[str, Any]:
        athlete_id = self.get_athlete_id()
        return self._get(f'{self._base_url}/athletes/{athlete_id}/stats')
