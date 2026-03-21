import json
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from coach.web.google_oauth import ChainlitGoogleOAuthProvider


class TestChainlitGoogleOAuthProvider:
    def setup_method(self) -> None:
        self.provider = ChainlitGoogleOAuthProvider()

    def test_openid_scope_is_added(self) -> None:
        assert 'openid' in self.provider.authorize_params['scope']

    def test_original_scopes_are_preserved(self) -> None:
        scope = self.provider.authorize_params['scope']
        assert 'userinfo.profile' in scope
        assert 'userinfo.email' in scope

    @pytest.mark.anyio
    async def test_get_token_encodes_both_tokens(self) -> None:
        self.provider.get_raw_token_response = AsyncMock(return_value={'access_token': 'acc-tok', 'id_token': 'id-tok'})  # type: ignore[method-assign]

        result = await self.provider.get_token('code', 'http://localhost/callback')

        tokens = json.loads(result)
        assert tokens['access_token'] == 'acc-tok'
        assert tokens['id_token'] == 'id-tok'

    @pytest.mark.anyio
    async def test_get_token_raises_when_access_token_missing(self) -> None:
        self.provider.get_raw_token_response = AsyncMock(return_value={'id_token': 'id-tok'})  # type: ignore[method-assign]

        with pytest.raises(HTTPException):
            await self.provider.get_token('code', 'http://localhost/callback')

    @pytest.mark.anyio
    async def test_get_user_info_embeds_id_token_in_raw_user_data(self) -> None:
        google_user_data: dict[str, Any] = {'email': 'user@example.com', 'name': 'Test User', 'picture': 'http://pic'}
        mock_user = MagicMock()
        encoded_token = json.dumps({'access_token': 'acc-tok', 'id_token': 'id-tok'})

        with patch('chainlit.oauth_providers.GoogleOAuthProvider.get_user_info', new=AsyncMock(return_value=(google_user_data, mock_user))):
            raw_user_data, user = await self.provider.get_user_info(encoded_token)

        assert raw_user_data['id_token'] == 'id-tok'
        assert raw_user_data['email'] == 'user@example.com'
        assert user is mock_user

    @pytest.mark.anyio
    async def test_get_user_info_calls_parent_with_access_token(self) -> None:
        google_user_data: dict[str, Any] = {'email': 'user@example.com', 'picture': 'http://pic'}
        mock_user = MagicMock()
        encoded_token = json.dumps({'access_token': 'acc-tok', 'id_token': 'id-tok'})

        with patch('chainlit.oauth_providers.GoogleOAuthProvider.get_user_info', new=AsyncMock(return_value=(google_user_data, mock_user))) as mock_parent:
            await self.provider.get_user_info(encoded_token)

        mock_parent.assert_called_once_with('acc-tok')
