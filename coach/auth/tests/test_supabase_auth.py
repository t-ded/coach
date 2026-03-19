import base64
import hashlib
from urllib.parse import parse_qs
from urllib.parse import urlparse

from coach.auth.supabase_auth import _build_auth_url
from coach.auth.supabase_auth import _generate_pkce_pair


class TestGeneratePkcePair:
    def test_verifier_is_url_safe_base64(self) -> None:
        verifier, _ = _generate_pkce_pair()
        # Should only contain URL-safe base64 characters (no padding)
        assert set(verifier) <= set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')

    def test_challenge_is_sha256_of_verifier(self) -> None:
        verifier, challenge = _generate_pkce_pair()
        digest = hashlib.sha256(verifier.encode()).digest()
        expected_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
        assert challenge == expected_challenge

    def test_each_call_produces_unique_pair(self) -> None:
        verifier1, _ = _generate_pkce_pair()
        verifier2, _ = _generate_pkce_pair()
        assert verifier1 != verifier2


class TestBuildAuthUrl:
    def test_targets_supabase_authorize_endpoint(self) -> None:
        url = _build_auth_url('https://example.supabase.co', 'challenge123')
        assert url.startswith('https://example.supabase.co/auth/v1/authorize')

    def test_includes_required_oauth_params(self) -> None:
        url = _build_auth_url('https://example.supabase.co', 'challenge123')
        params = parse_qs(urlparse(url).query)
        assert params['provider'] == ['google']
        assert params['code_challenge'] == ['challenge123']
        assert params['code_challenge_method'] == ['S256']
        assert params['response_type'] == ['code']

    def test_redirect_uri_points_to_localhost(self) -> None:
        url = _build_auth_url('https://example.supabase.co', 'challenge123')
        params = parse_qs(urlparse(url).query)
        assert params['redirect_to'][0].startswith('http://localhost:')
