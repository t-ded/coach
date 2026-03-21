from datetime import UTC
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock

from coach.web.auth import build_authenticated_client
from coach.web.auth import refresh_if_needed
from coach.web.auth import sign_in_with_supabase

_FIXED_EXPIRES_AT = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)


def _make_mock_client(*, access_token: str = 'access-123', refresh_token: str = 'refresh-456', user_id: str = 'user-uuid-789') -> MagicMock:
    mock_session = MagicMock()
    mock_session.access_token = access_token
    mock_session.refresh_token = refresh_token
    mock_session.expires_at = int(_FIXED_EXPIRES_AT.timestamp())

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_response = MagicMock()
    mock_response.session = mock_session
    mock_response.user = mock_user

    client = MagicMock()
    client.auth.sign_in_with_id_token.return_value = mock_response
    client.auth.refresh_session.return_value = mock_response
    return client


class TestSignInWithSupabase:
    def setup_method(self) -> None:
        self.client = _make_mock_client()

    def test_calls_sign_in_with_google_provider_and_token(self) -> None:
        sign_in_with_supabase('google-id-token', self.client)

        self.client.auth.sign_in_with_id_token.assert_called_once_with({'provider': 'google', 'token': 'google-id-token'})

    def test_returns_access_token(self) -> None:
        access, _, _, _ = sign_in_with_supabase('token', self.client)

        assert access == 'access-123'

    def test_returns_refresh_token(self) -> None:
        _, refresh, _, _ = sign_in_with_supabase('token', self.client)

        assert refresh == 'refresh-456'

    def test_returns_user_id(self) -> None:
        _, _, user_id, _ = sign_in_with_supabase('token', self.client)

        assert user_id == 'user-uuid-789'

    def test_returns_expires_at_as_utc_datetime(self) -> None:
        _, _, _, expires_at = sign_in_with_supabase('token', self.client)

        assert expires_at == _FIXED_EXPIRES_AT
        assert expires_at.tzinfo is UTC


class TestRefreshIfNeeded:
    def setup_method(self) -> None:
        self.client = _make_mock_client(access_token='new-access', refresh_token='new-refresh')

    def test_refreshes_when_near_expiry(self) -> None:
        near_expiry = datetime.now(UTC) + timedelta(minutes=3)

        access, refresh, _ = refresh_if_needed('old-access', 'old-refresh', near_expiry, self.client)

        self.client.auth.refresh_session.assert_called_once_with('old-refresh')
        assert access == 'new-access'
        assert refresh == 'new-refresh'

    def test_does_not_refresh_when_token_is_fresh(self) -> None:
        fresh_expiry = datetime.now(UTC) + timedelta(hours=1)

        access, refresh, expires_at = refresh_if_needed('old-access', 'old-refresh', fresh_expiry, self.client)

        self.client.auth.refresh_session.assert_not_called()
        assert access == 'old-access'
        assert refresh == 'old-refresh'
        assert expires_at == fresh_expiry

    def test_returns_updated_expires_at_after_refresh(self) -> None:
        near_expiry = datetime.now(UTC) + timedelta(minutes=3)

        _, _, expires_at = refresh_if_needed('old-access', 'old-refresh', near_expiry, self.client)

        assert expires_at == _FIXED_EXPIRES_AT


class TestBuildAuthenticatedClient:
    def test_sets_session_on_provided_client(self) -> None:
        base_client = MagicMock()

        result = build_authenticated_client('access-tok', 'refresh-tok', base_client)

        base_client.auth.set_session.assert_called_once_with(access_token='access-tok', refresh_token='refresh-tok')
        assert result is base_client
