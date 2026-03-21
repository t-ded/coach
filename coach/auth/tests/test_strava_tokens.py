import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path

import pytest

from coach.auth.strava_tokens import CredentialsStoreStravaTokenRepository
from coach.auth.strava_tokens import StravaTokens
from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.config.credentials import CredentialsStore

_EXPIRES_AT = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
_RPC_ROW = {
    'access_token': 'acc_token',
    'refresh_token': 'ref_token',
    'expires_at': _EXPIRES_AT.isoformat(),
}
_TOKENS = StravaTokens(access_token='acc_token', refresh_token='ref_token', expires_at=_EXPIRES_AT)


class TestSupabaseStravaTokenRepository:
    def setup_method(self) -> None:
        from unittest.mock import MagicMock
        self.client = MagicMock()
        self.repo = SupabaseStravaTokenRepository(self.client)

    def test_get_tokens_returns_none_when_no_tokens_stored(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = []
        result = self.repo.get_tokens('user-123')
        assert result is None

    def test_get_tokens_returns_strava_tokens_when_row_exists(self) -> None:
        self.client.rpc.return_value.execute.return_value.data = [_RPC_ROW]
        result = self.repo.get_tokens('user-123')
        assert result == StravaTokens(
            access_token='acc_token',
            refresh_token='ref_token',
            expires_at=_EXPIRES_AT,
        )

    def test_save_tokens_calls_upsert_rpc_with_correct_arguments(self) -> None:
        self.repo.save_tokens('user-123', _TOKENS)
        self.client.rpc.assert_called_once_with('upsert_strava_tokens', {
            'p_user_id': 'user-123',
            'p_access_token': 'acc_token',
            'p_refresh_token': 'ref_token',
            'p_expires_at': _EXPIRES_AT.isoformat(),
        })


class TestCredentialsStoreStravaTokenRepository:
    def setup_method(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = CredentialsStore(config_dir=Path(self._tmp.name))
        self.repo = CredentialsStoreStravaTokenRepository(self.store)

    def teardown_method(self) -> None:
        self._tmp.cleanup()

    def test_returns_none_when_no_credentials_stored(self) -> None:
        assert self.repo.get_tokens('any-user') is None

    def test_returns_tokens_from_stored_credentials(self) -> None:
        self.store.store_strava_credentials(
            client_id='cid', client_secret='csec',
            access_token='acc', refresh_token='ref', expires_at=1_800_000_000,
        )
        result = self.repo.get_tokens('any-user')
        assert result == StravaTokens(
            access_token='acc',
            refresh_token='ref',
            expires_at=datetime.fromtimestamp(1_800_000_000, tz=UTC),
        )

    def test_save_tokens_preserves_client_credentials(self) -> None:
        self.store.store_strava_credentials(
            client_id='cid', client_secret='csec',
            access_token='old_acc', refresh_token='old_ref', expires_at=1,
        )
        self.repo.save_tokens('any-user', _TOKENS)
        saved = self.store.get_strava_credentials()
        assert saved is not None
        assert saved['client_id'] == 'cid'
        assert saved['client_secret'] == 'csec'
        assert saved['access_token'] == 'acc_token'
        assert saved['refresh_token'] == 'ref_token'

    def test_save_tokens_with_no_prior_credentials_stores_empty_client_fields(self) -> None:
        self.repo.save_tokens('any-user', _TOKENS)
        saved = self.store.get_strava_credentials()
        assert saved is not None
        assert saved['client_id'] == ''
        assert saved['client_secret'] == ''
        assert saved['access_token'] == 'acc_token'
        assert saved['refresh_token'] == 'ref_token'
