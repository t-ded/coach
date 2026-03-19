import json
import os
from pathlib import Path
from typing import Any
from typing import Optional


class CredentialsStore:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = config_dir or Path(os.path.expanduser('~')) / '.coach'
        self._config_dir.mkdir(mode=0o700, exist_ok=True)
        self._credentials_file = self._config_dir / 'credentials.json'

        if self._credentials_file.exists():
            self._credentials_file.chmod(0o600)

    def store_strava_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str,
        expires_at: int,
    ) -> None:
        credentials = self._load_credentials()
        credentials['strava'] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at,
        }
        self._save_credentials(credentials)

    def get_strava_credentials(self) -> Optional[dict[str, Any]]:
        return self._load_credentials().get('strava')

    def has_strava_credentials(self) -> bool:
        return self.get_strava_credentials() is not None

    def store_google_api_key(self, api_key: str) -> None:
        credentials = self._load_credentials()
        credentials['google'] = {'api_key': api_key}
        self._save_credentials(credentials)

    def get_google_api_key(self) -> Optional[str]:
        google_creds = self._load_credentials().get('google')
        return google_creds.get('api_key') if google_creds else None

    def has_google_credentials(self) -> bool:
        return self.get_google_api_key() is not None

    def store_openai_api_key(self, api_key: str) -> None:
        credentials = self._load_credentials()
        credentials['openai'] = {'api_key': api_key}
        self._save_credentials(credentials)

    def get_openai_api_key(self) -> Optional[str]:
        openai_creds = self._load_credentials().get('openai')
        return openai_creds.get('api_key') if openai_creds else None

    def has_openai_credentials(self) -> bool:
        return self.get_openai_api_key() is not None

    def store_supabase_session(self, *, access_token: str, refresh_token: str) -> None:
        credentials = self._load_credentials()
        credentials['supabase'] = {'access_token': access_token, 'refresh_token': refresh_token}
        self._save_credentials(credentials)

    def get_supabase_session(self) -> Optional[dict[str, str]]:
        supabase = self._load_credentials().get('supabase')
        if supabase is None:
            return None
        return {'access_token': supabase['access_token'], 'refresh_token': supabase['refresh_token']}

    def has_supabase_session(self) -> bool:
        return self.get_supabase_session() is not None

    def _load_credentials(self) -> dict[str, Any]:
        if not self._credentials_file.exists():
            return {}

        with self._credentials_file.open('r') as f:
            return json.load(f)

    def _save_credentials(self, credentials: dict[str, Any]) -> None:
        with self._credentials_file.open('w') as f:
            json.dump(credentials, f, indent=2)
        self._credentials_file.chmod(0o600)
