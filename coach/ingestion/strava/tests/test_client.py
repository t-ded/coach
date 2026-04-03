from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.client import StravaRateLimitError
from coach.ingestion.strava.client import StravaTokenRevokedError


def _make_client() -> StravaClient:
    token_repo = MagicMock()
    token_repo.get_tokens.return_value = MagicMock(
        access_token='test-token',
        refresh_token='ref',
        expires_at=MagicMock(timestamp=lambda: 9999999999),
    )
    with patch('coach.ingestion.strava.client.StravaAuth') as mock_auth_cls:
        mock_auth_cls.return_value.get_access_token.return_value = 'test-token'
        client = StravaClient(user_id='user-1', token_repo=token_repo)
        client._auth = mock_auth_cls.return_value
    return client


def _response(status: int, headers: dict | None = None, json_data: object = None) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


class TestStravaClientRateLimitLogging:
    def test_logs_rate_limit_on_successful_response(self, caplog: pytest.LogCaptureFixture) -> None:
        client = _make_client()
        resp = _response(
            200,
            headers={'X-RateLimit-Usage': '10,100', 'X-RateLimit-Limit': '200,2000'},
            json_data={'id': 1},
        )

        with patch('requests.get', return_value=resp), caplog.at_level('DEBUG', logger='coach.ingestion.strava.client'):
            client._get('https://example.com/test')

        assert '10/200' in caplog.text
        assert '100/2000' in caplog.text

    def test_no_log_when_headers_absent(self, caplog: pytest.LogCaptureFixture) -> None:
        client = _make_client()
        resp = _response(200, headers={}, json_data={'id': 1})

        with patch('requests.get', return_value=resp), caplog.at_level('DEBUG', logger='coach.ingestion.strava.client'):
            client._get('https://example.com/test')

        assert 'rate limit' not in caplog.text.lower()


class TestStravaClientTokenRevoked:
    def test_raises_token_revoked_error_on_401(self) -> None:
        client = _make_client()
        resp = _response(401)

        with patch('requests.get', return_value=resp), pytest.raises(StravaTokenRevokedError):
            client._get('https://example.com/test')

    def test_does_not_raise_rate_limit_error_on_401(self) -> None:
        client = _make_client()
        resp = _response(401)

        with patch('requests.get', return_value=resp), pytest.raises(StravaTokenRevokedError):
            client._get('https://example.com/test')

    def test_raises_rate_limit_error_on_429(self) -> None:
        client = _make_client()
        resp = _response(429, headers={'X-RateLimit-Usage': '200,500', 'X-RateLimit-Limit': '200,2000'})

        with patch('requests.get', return_value=resp), patch('time.sleep'), pytest.raises(StravaRateLimitError):
            client._get('https://example.com/test')
