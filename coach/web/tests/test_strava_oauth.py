import os
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

from fastapi.testclient import TestClient

from coach.persistence.database import create_secret_client
from coach.web.app import create_app
from coach.web.strava_oauth import generate_strava_auth_url

_VALID_TOKEN_DATA: dict[str, Any] = {
    'access_token': 'access-abc',
    'refresh_token': 'refresh-xyz',
    'expires_at': 9999999999,
    'athlete': {'id': 42},
}


class TestStravaOAuthCallback:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()
        app = create_app()
        app.dependency_overrides[create_secret_client] = lambda: self._secret_client
        self._client = TestClient(app, raise_server_exceptions=False)

    def _setup_state_row(self, expires_at: datetime) -> None:
        result = MagicMock()
        result.data = [{'user_id': 'user-123', 'state': 'valid-state', 'expires_at': expires_at.isoformat()}]
        self._secret_client.table.return_value.select.return_value.eq.return_value.execute.return_value = result

    def test_rejects_missing_state(self) -> None:
        result = MagicMock()
        result.data = []
        self._secret_client.table.return_value.select.return_value.eq.return_value.execute.return_value = result

        response = self._client.get('/auth/strava/callback?code=abc&state=bogus')

        assert response.status_code == 400

    def test_rejects_expired_state(self) -> None:
        self._setup_state_row(expires_at=datetime.now(UTC) - timedelta(hours=1))

        response = self._client.get('/auth/strava/callback?code=abc&state=valid-state')

        assert response.status_code == 400

    def test_happy_path_redirects_to_chainlit(self) -> None:
        self._setup_state_row(expires_at=datetime.now(UTC) + timedelta(hours=1))

        with patch('coach.web.strava_oauth._exchange_code_for_tokens', return_value=_VALID_TOKEN_DATA), patch.dict(os.environ, {'CHAINLIT_URL': 'http://localhost:9000'}):
            response = self._client.get('/auth/strava/callback?code=abc&state=valid-state', follow_redirects=False)

        assert response.status_code in (302, 307)
        assert response.headers['location'] == 'http://localhost:9000'

    def test_happy_path_stores_tokens(self) -> None:
        self._setup_state_row(expires_at=datetime.now(UTC) + timedelta(hours=1))

        with patch('coach.web.strava_oauth._exchange_code_for_tokens', return_value=_VALID_TOKEN_DATA):
            self._client.get('/auth/strava/callback?code=abc&state=valid-state')

        self._secret_client.rpc.assert_called()

    def test_happy_path_updates_strava_user_id(self) -> None:
        self._setup_state_row(expires_at=datetime.now(UTC) + timedelta(hours=1))

        with patch('coach.web.strava_oauth._exchange_code_for_tokens', return_value=_VALID_TOKEN_DATA):
            self._client.get('/auth/strava/callback?code=abc&state=valid-state')

        self._secret_client.table.return_value.update.assert_called_once_with({'strava_user_id': 42})


class TestGenerateStravaAuthUrl:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()

    def test_inserts_state_row_for_user(self) -> None:
        with patch.dict(os.environ, {'STRAVA_CLIENT_ID': 'test-client-id'}):
            generate_strava_auth_url('user-123', self._secret_client)

        insert_call = self._secret_client.table.return_value.insert.call_args[0][0]
        assert insert_call['user_id'] == 'user-123'
        assert 'state' in insert_call
        assert 'expires_at' in insert_call

    def test_url_contains_required_oauth_params(self) -> None:
        with patch.dict(os.environ, {'STRAVA_CLIENT_ID': 'test-client-id', 'STRAVA_REDIRECT_URI': 'http://localhost:8000/auth/strava/callback'}):
            url = generate_strava_auth_url('user-123', self._secret_client)

        assert 'strava.com' in url
        assert 'client_id=test-client-id' in url
        assert 'redirect_uri=' in url
        assert 'scope=activity%3Aread_all' in url
        assert 'state=' in url
