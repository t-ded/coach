import os
from unittest.mock import MagicMock
from unittest.mock import patch

from fastapi.testclient import TestClient

from coach.persistence.database import create_secret_client
from coach.web.app import create_app

_VERIFY_TOKEN = 'test-verify-token'


def _make_test_client() -> tuple[TestClient, MagicMock]:
    secret_client = MagicMock()
    app = create_app()
    app.dependency_overrides[create_secret_client] = lambda: secret_client
    return TestClient(app, raise_server_exceptions=False), secret_client


class TestStravaWebhookChallenge:
    def setup_method(self) -> None:
        self._http, self._secret_client = _make_test_client()

    def test_valid_token_returns_challenge(self) -> None:
        with patch.dict(os.environ, {'STRAVA_WEBHOOK_VERIFY_TOKEN': _VERIFY_TOKEN}):
            response = self._http.get(f'/webhook/strava?hub.challenge=abc123&hub.verify_token={_VERIFY_TOKEN}')

        assert response.status_code == 200
        assert response.json() == {'hub.challenge': 'abc123'}

    def test_invalid_token_returns_403(self) -> None:
        with patch.dict(os.environ, {'STRAVA_WEBHOOK_VERIFY_TOKEN': _VERIFY_TOKEN}):
            response = self._http.get('/webhook/strava?hub.challenge=abc123&hub.verify_token=wrong')

        assert response.status_code == 403

    def test_missing_env_var_returns_500(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != 'STRAVA_WEBHOOK_VERIFY_TOKEN'}
        with patch.dict(os.environ, env, clear=True):
            response = self._http.get('/webhook/strava?hub.challenge=abc123&hub.verify_token=anything')

        assert response.status_code == 500


class TestStravaWebhookEvent:
    def setup_method(self) -> None:
        self._http, self._secret_client = _make_test_client()

    def test_deauthorization_event_calls_deauthorize(self) -> None:
        with patch('coach.web.strava_webhook.deauthorize_athlete') as mock_deauth:
            response = self._http.post(
                '/webhook/strava',
                json={
                    'object_type': 'athlete',
                    'aspect_type': 'deauthorization',
                    'owner_id': 42,
                    'object_id': 42,
                },
            )

        assert response.status_code == 200
        mock_deauth.assert_called_once_with(42, mock_deauth.call_args[0][1])

    def test_activity_create_event_dispatches_handler(self) -> None:
        with patch('coach.web.strava_webhook._handle_activity_event') as mock_handler:
            response = self._http.post(
                '/webhook/strava',
                json={
                    'object_type': 'activity',
                    'aspect_type': 'create',
                    'owner_id': 42,
                    'object_id': 999,
                },
            )

        assert response.status_code == 200
        mock_handler.assert_called_once_with('create', 42, 999, mock_handler.call_args[0][3])

    def test_activity_update_event_dispatches_handler(self) -> None:
        with patch('coach.web.strava_webhook._handle_activity_event') as mock_handler:
            response = self._http.post(
                '/webhook/strava',
                json={
                    'object_type': 'activity',
                    'aspect_type': 'update',
                    'owner_id': 42,
                    'object_id': 999,
                },
            )

        assert response.status_code == 200
        mock_handler.assert_called_once()

    def test_activity_delete_event_dispatches_handler(self) -> None:
        with patch('coach.web.strava_webhook._handle_activity_event') as mock_handler:
            response = self._http.post(
                '/webhook/strava',
                json={
                    'object_type': 'activity',
                    'aspect_type': 'delete',
                    'owner_id': 42,
                    'object_id': 999,
                },
            )

        assert response.status_code == 200
        mock_handler.assert_called_once_with('delete', 42, 999, mock_handler.call_args[0][3])

    def test_unrecognised_event_returns_200(self) -> None:
        response = self._http.post(
            '/webhook/strava',
            json={
                'object_type': 'something_new',
                'aspect_type': 'unknown',
            },
        )

        assert response.status_code == 200

    def test_missing_owner_id_returns_200(self) -> None:
        response = self._http.post(
            '/webhook/strava',
            json={
                'object_type': 'activity',
                'aspect_type': 'create',
                'object_id': 999,
            },
        )

        assert response.status_code == 200


class TestHandleActivityEvent:
    def setup_method(self) -> None:
        self._secret_client = MagicMock()
        self._activity_repo = MagicMock()
        self._strava_client = MagicMock()
        self._strava_client.get_detailed_activity.return_value = {
            'id': 999,
            'start_date': '2024-01-01T07:00:00Z',
            'elapsed_time': 3600,
            'sport_type': 'Run',
            'type': 'Run',
        }

    def _run(self, aspect_type: str) -> None:
        from coach.web.strava_webhook import _handle_activity_event

        with (
            patch('coach.web.strava_webhook.SupabaseUsersRepository.find_user_id_by_strava_id', return_value='user-1'),
            patch('coach.web.strava_webhook.SupabaseActivityRepository', return_value=self._activity_repo),
            patch('coach.web.strava_webhook.StravaClient', return_value=self._strava_client),
        ):
            _handle_activity_event(aspect_type, owner_id=42, object_id=999, secret_client=self._secret_client)

    def test_delete_calls_delete_by_strava_id(self) -> None:
        self._run('delete')
        self._activity_repo.delete_by_strava_id.assert_called_once_with(999)

    def test_create_fetches_and_saves_activity(self) -> None:
        self._run('create')
        self._strava_client.get_detailed_activity.assert_called_once_with(999)
        self._activity_repo.save.assert_called_once()

    def test_update_fetches_and_saves_activity(self) -> None:
        self._run('update')
        self._strava_client.get_detailed_activity.assert_called_once_with(999)
        self._activity_repo.save.assert_called_once()

    def test_unknown_user_is_ignored(self) -> None:
        from coach.web.strava_webhook import _handle_activity_event

        with patch('coach.web.strava_webhook.SupabaseUsersRepository.find_user_id_by_strava_id', return_value=None):
            _handle_activity_event('create', owner_id=99, object_id=999, secret_client=self._secret_client)

        self._activity_repo.save.assert_not_called()
