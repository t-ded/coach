import os
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi import Request
from fastapi.testclient import TestClient
from httpx import Response
from jwt.exceptions import PyJWTError

from coach.persistence.database import create_secret_client
from coach.web.api_key_routes import _verify_caller
from coach.web.api_key_routes import generate_api_key_form_url
from coach.web.app import create_app

_VALID_EXPIRES = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
_EXPIRED_AT = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
_USER_ID = 'user-123'


class TestApiKeyForm:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()
        app = create_app()
        app.dependency_overrides[create_secret_client] = lambda: self._secret_client
        self._client = TestClient(app, raise_server_exceptions=False)

        self._verify_patcher = patch('coach.web.api_key_routes._verify_caller')
        self._verify_patcher.start()

    def teardown_method(self) -> None:
        self._verify_patcher.stop()

    def _setup_state(self, expires_at: str) -> None:
        result = MagicMock()
        result.data = [{'user_id': _USER_ID, 'expires_at': expires_at}]
        self._secret_client.table.return_value.select.return_value.eq.return_value.execute.return_value = result

    def test_valid_state_renders_form(self) -> None:
        self._setup_state(_VALID_EXPIRES)
        response = self._client.get('/api-key?state=valid-state')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert '<input type="password"' in response.text

    def test_form_contains_all_providers(self) -> None:
        self._setup_state(_VALID_EXPIRES)
        response = self._client.get('/api-key?state=valid-state')
        assert 'google' in response.text
        assert 'openai' in response.text.lower()
        assert 'anthropic' in response.text.lower()

    def test_invalid_state_returns_400(self) -> None:
        result = MagicMock()
        result.data = []
        self._secret_client.table.return_value.select.return_value.eq.return_value.execute.return_value = result
        response = self._client.get('/api-key?state=bogus')
        assert response.status_code == 400

    def test_expired_state_returns_400(self) -> None:
        self._setup_state(_EXPIRED_AT)
        response = self._client.get('/api-key?state=expired-state')
        assert response.status_code == 400

    def test_error_param_is_shown_in_form(self) -> None:
        self._setup_state(_VALID_EXPIRES)
        response = self._client.get('/api-key?state=valid-state&error=Key+not+valid')
        assert response.status_code == 200
        assert 'Key not valid' in response.text


class TestApiKeyStore:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()
        app = create_app()
        app.dependency_overrides[create_secret_client] = lambda: self._secret_client
        self._client = TestClient(app, raise_server_exceptions=False)

        self._state_patcher = patch('coach.web.api_key_routes._lookup_state', return_value=_USER_ID)
        self._state_mock = self._state_patcher.start()

        self._verify_patcher = patch('coach.web.api_key_routes._verify_caller')
        self._verify_patcher.start()

        self._validate_patcher = patch('coach.web.api_key_routes._validate_api_key', return_value=True)
        self._validate_mock = self._validate_patcher.start()

        # No existing keys by default (first key scenario)
        self._secret_client.rpc.return_value.execute.return_value.data = []

    def teardown_method(self) -> None:
        self._state_patcher.stop()
        self._verify_patcher.stop()
        self._validate_patcher.stop()

    def _post(self, provider: str = 'google', api_key: str = 'test-key', state: str = 'valid-state') -> Response:
        return self._client.post(
            '/api-key/store',
            data={'state': state, 'provider': provider, 'api_key': api_key},
            follow_redirects=False,
        )

    def test_valid_submission_redirects_to_chainlit(self) -> None:
        with patch.dict(os.environ, {'CHAINLIT_URL': 'http://localhost:9000'}):
            response = self._post()
        assert response.status_code == 303
        assert response.headers['location'] == 'http://localhost:9000'

    def test_valid_submission_saves_key(self) -> None:
        self._post()
        self._secret_client.rpc.assert_any_call(
            'upsert_ai_key',
            {'p_user_id': _USER_ID, 'p_provider': 'google', 'p_api_key': 'test-key'},
        )

    def test_first_key_sets_preferred_provider(self) -> None:
        self._secret_client.rpc.return_value.execute.return_value.data = []
        self._post(provider='openai')
        self._secret_client.table.return_value.upsert.assert_called_once_with(
            {'user_id': _USER_ID, 'preferred_provider': 'openai'},
            on_conflict='user_id',
        )

    def test_subsequent_key_does_not_change_preferred_provider(self) -> None:
        self._secret_client.rpc.return_value.execute.return_value.data = [{'provider': 'google'}]
        self._post(provider='openai')
        self._secret_client.table.return_value.upsert.assert_not_called()

    def test_invalid_state_returns_400(self) -> None:
        self._state_patcher.stop()
        result = MagicMock()
        result.data = []
        self._secret_client.table.return_value.select.return_value.eq.return_value.execute.return_value = result
        response = self._post(state='bogus')
        assert response.status_code == 400
        self._state_patcher = patch('coach.web.api_key_routes._lookup_state', return_value=_USER_ID)
        self._state_mock = self._state_patcher.start()

    def test_key_validation_failure_returns_form_with_error(self) -> None:
        self._validate_mock.return_value = False
        response = self._post()
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'could not be verified' in response.text

    def test_key_validation_failure_preserves_provider_selection(self) -> None:
        self._validate_mock.return_value = False
        response = self._post(provider='openai')
        assert response.status_code == 200
        assert 'value="openai" selected' in response.text
        assert 'value="google" selected' not in response.text

    def test_unknown_provider_returns_400(self) -> None:
        response = self._post(provider='unknown-provider')
        assert response.status_code == 400

    def test_state_is_consumed_on_success(self) -> None:
        self._post()
        self._secret_client.table.return_value.delete.assert_called()


class TestGenerateApiKeyFormUrl:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()

    def test_inserts_state_row_for_user(self) -> None:
        generate_api_key_form_url(_USER_ID, self._secret_client)
        insert_call = self._secret_client.table.return_value.insert.call_args[0][0]
        assert insert_call['user_id'] == _USER_ID
        assert 'state' in insert_call
        assert 'expires_at' in insert_call

    def test_url_contains_state_param(self) -> None:
        url = generate_api_key_form_url(_USER_ID, self._secret_client)
        assert '/oauth/api-key?state=' in url

    def test_url_uses_chainlit_url_env(self) -> None:
        with patch.dict(os.environ, {'CHAINLIT_URL': 'https://myapp.com'}):
            url = generate_api_key_form_url(_USER_ID, self._secret_client)
        assert url.startswith('https://myapp.com')

    def test_url_includes_provider_when_specified(self) -> None:
        url = generate_api_key_form_url(_USER_ID, self._secret_client, provider='openai')
        assert 'provider=openai' in url

    def test_url_omits_provider_param_when_not_specified(self) -> None:
        url = generate_api_key_form_url(_USER_ID, self._secret_client)
        assert 'provider=' not in url


class TestVerifyCaller:
    def _make_request(self, cookies: dict) -> Request:
        mock = MagicMock(spec=Request)
        mock.cookies = cookies
        return mock

    def test_no_cookie_raises_403(self) -> None:
        request = self._make_request({})
        with patch('coach.web.api_key_routes.get_token_from_cookies', return_value=None), pytest.raises(HTTPException) as exc_info:
            _verify_caller(request, _USER_ID)
        assert exc_info.value.status_code == 403

    def test_invalid_token_raises_403(self) -> None:
        request = self._make_request({'access_token': 'bad'})
        with (
            patch('coach.web.api_key_routes.get_token_from_cookies', return_value='bad'),
            patch('coach.web.api_key_routes.decode_jwt', side_effect=PyJWTError('invalid')),
            pytest.raises(HTTPException) as exc_info,
        ):
            _verify_caller(request, _USER_ID)
        assert exc_info.value.status_code == 403

    def test_mismatched_user_id_raises_403(self) -> None:
        user = MagicMock()
        user.metadata = {'supabase_user_id': 'other-user'}
        request = self._make_request({'access_token': 'valid'})
        with (
            patch('coach.web.api_key_routes.get_token_from_cookies', return_value='valid'),
            patch('coach.web.api_key_routes.decode_jwt', return_value=user),
            pytest.raises(HTTPException) as exc_info,
        ):
            _verify_caller(request, _USER_ID)
        assert exc_info.value.status_code == 403

    def test_matching_user_id_passes(self) -> None:
        user = MagicMock()
        user.metadata = {'supabase_user_id': _USER_ID}
        request = self._make_request({'access_token': 'valid'})
        with patch('coach.web.api_key_routes.get_token_from_cookies', return_value='valid'), patch('coach.web.api_key_routes.decode_jwt', return_value=user):
            _verify_caller(request, _USER_ID)  # should not raise
