from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Optional
from unittest.mock import MagicMock

import pytest

from coach.auth.strava_tokens import StravaTokenRepository
from coach.auth.strava_tokens import StravaTokens


def _make_tokens(*, expired: bool) -> StravaTokens:
    delta = timedelta(hours=-1) if expired else timedelta(hours=1)
    return StravaTokens(
        access_token='acc_token',
        refresh_token='ref_token',
        expires_at=datetime.now(UTC) + delta,
    )


class FakeStravaTokenRepository(StravaTokenRepository):
    def __init__(self) -> None:
        self._tokens: dict[str, StravaTokens] = {}

    def get_tokens(self, user_id: str) -> Optional[StravaTokens]:
        return self._tokens.get(user_id)

    def save_tokens(self, user_id: str, tokens: StravaTokens) -> None:
        self._tokens[user_id] = tokens


class TestStravaAuth:
    def setup_method(self) -> None:
        from coach.auth.strava import StravaAuth
        self.repo = FakeStravaTokenRepository()
        self.auth = StravaAuth(user_id='user-123', token_repo=self.repo)

    def test_returns_access_token_from_repository(self) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=False))
        token = self.auth.get_access_token()
        assert token == 'acc_token'

    def test_raises_when_no_tokens_stored(self) -> None:
        with pytest.raises(RuntimeError):
            self.auth.get_access_token()

    def test_refreshes_and_saves_when_token_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=True))

        refreshed_payload = {
            'access_token': 'new_acc',
            'refresh_token': 'new_ref',
            'expires_at': int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
        }
        mock_post = MagicMock()
        mock_post.return_value.json.return_value = refreshed_payload
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        token = self.auth.get_access_token()

        assert token == 'new_acc'
        saved = self.repo.get_tokens('user-123')
        assert saved is not None
        assert saved.access_token == 'new_acc'
        assert saved.refresh_token == 'new_ref'

    def test_refresh_raises_when_response_missing_access_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=True))

        mock_post = MagicMock()
        mock_post.return_value.json.return_value = {'error': 'bad_request'}
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        with pytest.raises(RuntimeError, match='Strava token refresh failed'):
            self.auth.get_access_token()
