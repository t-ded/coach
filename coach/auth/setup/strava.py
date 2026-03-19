import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from typing import Any
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse

import requests

from coach.config.credentials import CredentialsStore

STRAVA_AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_OAUTH_ENDPOINT = 'https://www.strava.com/oauth/token'
REDIRECT_PORT = 8765
REDIRECT_URI = f'http://localhost:{REDIRECT_PORT}/callback'


def setup_strava_oauth() -> int:
    """Run Strava OAuth flow. Returns the authenticated athlete's Strava user ID."""
    print('\n=== Strava Setup ===')
    print('You will need a Strava API application. If you have not created one,')
    print('visit: https://www.strava.com/settings/api\n')

    client_id = input('Enter your Strava Client ID: ').strip()
    client_secret = input('Enter your Strava Client Secret: ').strip()

    if not client_id or not client_secret:
        raise ValueError('Client ID and Client Secret cannot be empty.')

    auth_code = _run_oauth_flow(client_id)
    token_data = _exchange_code_for_tokens(auth_code, client_id, client_secret)

    CredentialsStore().store_strava_credentials(
        client_id=client_id,
        client_secret=client_secret,
        access_token=token_data['access_token'],
        refresh_token=token_data['refresh_token'],
        expires_at=token_data['expires_at'],
    )

    print('\n✓ Strava authorization successful!')
    print('Credentials stored securely in ~/.coach/credentials.json')

    return int(token_data['athlete']['id'])


def _run_oauth_flow(client_id: str) -> str:
    state = secrets.token_urlsafe(32)
    auth_url = f'{STRAVA_AUTHORIZE_URL}?{urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "activity:read_all",
        "state": state,
    })}'

    print('\nOpening browser for Strava authorization...')
    print(f'If the browser does not open, visit: {auth_url}\n')
    webbrowser.open(auth_url)

    handler = _run_callback_server()

    if handler.state != state:
        raise ValueError('State mismatch — possible CSRF attack')
    if not handler.authorization_code:
        raise ValueError('No authorization code received')

    return handler.authorization_code


class _CallbackHandler(BaseHTTPRequestHandler):
    authorization_code: str | None = None
    state: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == '/callback':
            _CallbackHandler.authorization_code = params.get('code', [None])[0]
            _CallbackHandler.state = params.get('state', [None])[0]
            self._send_success_page()
        else:
            self.send_response(404)
            self.end_headers()

    def _send_success_page(self) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(
            b'<html><body><h1>Authentication successful!</h1>'
            b'<p>You can close this window and return to the terminal.</p></body></html>',
        )

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def _run_callback_server() -> _CallbackHandler:
    server = HTTPServer(('localhost', REDIRECT_PORT), _CallbackHandler)
    print(f'Waiting for authorization on port {REDIRECT_PORT}...')
    server.handle_request()
    server.server_close()
    return server.RequestHandlerClass  # type: ignore[return-value]


def _exchange_code_for_tokens(auth_code: str, client_id: str, client_secret: str) -> dict[str, Any]:
    response = requests.post(
        STRAVA_OAUTH_ENDPOINT,
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
