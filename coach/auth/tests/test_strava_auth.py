from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Optional
from unittest.mock import MagicMock

import pytest

from coach.auth.strava import StravaAuth
from coach.auth.strava_tokens import StravaTokenRepository
from coach.auth.strava_tokens import StravaTokens
from coach.ingestion.strava.client import StravaTokenRevokedError


def _make_tokens(*, expired: bool = False, near_expiry: bool = False) -> StravaTokens:
    if expired:
        delta = timedelta(hours=-1)
    elif near_expiry:
        delta = timedelta(minutes=3)  # within the 5-minute buffer
    else:
        delta = timedelta(hours=1)
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

    def delete_tokens(self, user_id: str) -> None:
        self._tokens.pop(user_id, None)


class TestStravaAuth:
    def setup_method(self) -> None:
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
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = refreshed_payload
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        token = self.auth.get_access_token()

        assert token == 'new_acc'
        saved = self.repo.get_tokens('user-123')
        assert saved is not None
        assert saved.access_token == 'new_acc'
        assert saved.refresh_token == 'new_ref'

    def test_refreshes_when_token_within_expiry_buffer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(near_expiry=True))

        refreshed_payload = {
            'access_token': 'new_acc',
            'refresh_token': 'new_ref',
            'expires_at': int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
        }
        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = refreshed_payload
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        token = self.auth.get_access_token()

        assert token == 'new_acc'
        mock_post.assert_called_once()

    def test_does_not_refresh_when_token_has_plenty_of_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=False))

        mock_post = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        self.auth.get_access_token()

        mock_post.assert_not_called()

    def test_refresh_raises_token_revoked_error_on_400(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=True))

        mock_post = MagicMock()
        mock_post.return_value.status_code = 400
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        with pytest.raises(StravaTokenRevokedError):
            self.auth.get_access_token()

    def test_refresh_raises_when_response_missing_access_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.repo.save_tokens('user-123', _make_tokens(expired=True))

        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'error': 'bad_request'}
        mock_post.return_value.raise_for_status = MagicMock()
        monkeypatch.setattr('coach.auth.strava.requests.post', mock_post)

        with pytest.raises(RuntimeError, match='Strava token refresh failed'):
            self.auth.get_access_token()
