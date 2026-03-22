"""Patches Chainlit's Google OAuth provider to capture the OIDC id_token.

Chainlit's default GoogleOAuthProvider omits the `openid` scope, so Google
never returns an id_token and Supabase's sign_in_with_id_token cannot be used.
This module subclasses the provider to request the scope and thread-safely
propagates the id_token through to the oauth_callback via raw_user_data.
"""

import json
from typing import Any

import chainlit.oauth_providers as _chainlit_providers
from chainlit.oauth_providers import GoogleOAuthProvider
from fastapi import HTTPException


class ChainlitGoogleOAuthProvider(GoogleOAuthProvider):
    def __init__(self) -> None:
        super().__init__()
        self.authorize_params['scope'] += ' openid'

    async def get_token(self, code: str, url: str) -> str:
        raw = await self.get_raw_token_response(code, url)
        access_token = raw.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail='Access token missing in the response')
        return json.dumps({'access_token': access_token, 'id_token': raw.get('id_token')})  # noqa: S105

    async def get_user_info(self, token: str) -> tuple[dict[str, Any], Any]:
        tokens: dict[str, Any] = json.loads(token)
        raw_user_data, user = await super().get_user_info(tokens['access_token'])
        if id_token := tokens.get('id_token'):  # noqa: S105
            raw_user_data['id_token'] = id_token  # noqa: S105
        return raw_user_data, user


def install_patched_google_provider() -> None:
    providers = _chainlit_providers.providers
    for i, provider in enumerate(providers):
        if provider.id == 'google':
            providers[i] = ChainlitGoogleOAuthProvider()
            return
