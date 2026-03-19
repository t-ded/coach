import base64
import hashlib
import os
import webbrowser
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse

from supabase import create_client

from coach.config.credentials import CredentialsStore

_CALLBACK_PORT = 8585
_CALLBACK_PATH = '/callback'
_REDIRECT_URI = f'http://localhost:{_CALLBACK_PORT}{_CALLBACK_PATH}'


def setup_supabase_login() -> None:
    supabase_url = os.environ['SUPABASE_URL']
    anon_key = os.environ['SUPABASE_ANON_KEY']
    client = create_client(supabase_url, anon_key)

    code_verifier, code_challenge = _generate_pkce_pair()
    auth_url = _build_auth_url(supabase_url, code_challenge)

    print('\n=== Supabase Login ===')
    print('Opening browser for Google login...')
    print(f'If the browser does not open, visit:\n  {auth_url}\n')
    webbrowser.open(auth_url)

    print(f'Waiting for authorization on port {_CALLBACK_PORT}...')
    auth_code = _capture_auth_code()

    response = client.auth.exchange_code_for_session({'auth_code': auth_code, 'code_verifier': code_verifier, 'redirect_to': _REDIRECT_URI})
    if response.session is None or response.user is None:
        raise RuntimeError('Authentication failed: no session returned')

    CredentialsStore().store_supabase_session(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
    )

    email = response.user.email or 'unknown'
    print(f'\n✓ Logged in as {email}')
    print('Session stored securely in ~/.coach/credentials.json')


def _generate_pkce_pair() -> tuple[str, str]:
    raw = os.urandom(32)
    code_verifier = base64.urlsafe_b64encode(raw).rstrip(b'=').decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return code_verifier, code_challenge


def _build_auth_url(supabase_url: str, code_challenge: str) -> str:
    params = urlencode({
        'provider': 'google',
        'redirect_to': _REDIRECT_URI,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'response_type': 'code',
    })
    return f'{supabase_url}/auth/v1/authorize?{params}'


def _capture_auth_code() -> str:
    code_holder: list[str] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == _CALLBACK_PATH:
                params = parse_qs(parsed.query)
                if 'code' in params:
                    code_holder.append(params['code'][0])
                    self._send_response_page(200, b'<h1>Authentication successful!</h1><p>You can close this window and return to the terminal.</p>')
                else:
                    error = params.get('error_description', params.get('error', ['Unknown error']))[0]
                    self._send_response_page(400, f'<h1>Authentication failed: {error}</h1>'.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def _send_response_page(self, status: int, body: bytes) -> None:
            self.send_response(status)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass

    server = HTTPServer(('localhost', _CALLBACK_PORT), _Handler)
    server.handle_request()
    server.server_close()

    if not code_holder:
        raise RuntimeError('No authorization code received — authentication may have failed or timed out')

    return code_holder[0]
