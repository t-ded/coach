from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock

from coach.auth.strava_tokens import StravaTokens
from coach.auth.strava_tokens import SupabaseStravaTokenRepository

_EXPIRES_AT = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
_RPC_ROW = {
    'access_token': 'acc_token',
    'refresh_token': 'ref_token',
    'expires_at': _EXPIRES_AT.isoformat(),
}
_TOKENS = StravaTokens(access_token='acc_token', refresh_token='ref_token', expires_at=_EXPIRES_AT)


class TestSupabaseStravaTokenRepository:
    def setup_method(self) -> None:
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
        self.client.rpc.assert_called_once_with(
            'upsert_strava_tokens',
            {
                'p_user_id': 'user-123',
                'p_access_token': 'acc_token',
                'p_refresh_token': 'ref_token',
                'p_expires_at': _EXPIRES_AT.isoformat(),
            },
        )
