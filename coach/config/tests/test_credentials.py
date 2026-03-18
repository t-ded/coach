from pathlib import Path

import pytest

from coach.config.credentials import CredentialsStore


@pytest.fixture
def store(tmp_path: Path) -> CredentialsStore:
    return CredentialsStore(config_dir=tmp_path)


class TestCredentialsStoreStrava:
    def test_has_no_credentials_initially(self, store: CredentialsStore) -> None:
        assert store.has_strava_credentials() is False
        assert store.get_strava_credentials() is None

    def test_store_and_retrieve(self, store: CredentialsStore) -> None:
        store.store_strava_credentials(
            client_id='id',
            client_secret='secret',
            access_token='access',
            refresh_token='refresh',
            expires_at=9999999999,
        )
        assert store.has_strava_credentials() is True
        creds = store.get_strava_credentials()
        assert creds is not None
        assert creds['client_id'] == 'id'
        assert creds['refresh_token'] == 'refresh'
        assert creds['expires_at'] == 9999999999

    def test_overwrite_existing_credentials(self, store: CredentialsStore) -> None:
        store.store_strava_credentials(client_id='old', client_secret='s', access_token='a', refresh_token='r', expires_at=1)
        store.store_strava_credentials(client_id='new', client_secret='s', access_token='a', refresh_token='r', expires_at=1)
        assert store.get_strava_credentials()['client_id'] == 'new'  # type: ignore[index]


class TestCredentialsStoreGoogle:
    def test_has_no_credentials_initially(self, store: CredentialsStore) -> None:
        assert store.has_google_credentials() is False
        assert store.get_google_api_key() is None

    def test_store_and_retrieve(self, store: CredentialsStore) -> None:
        store.store_google_api_key('ggl-key')
        assert store.has_google_credentials() is True
        assert store.get_google_api_key() == 'ggl-key'

    def test_overwrite_existing_key(self, store: CredentialsStore) -> None:
        store.store_google_api_key('old-key')
        store.store_google_api_key('new-key')
        assert store.get_google_api_key() == 'new-key'


class TestCredentialsStoreOpenAI:
    def test_has_no_credentials_initially(self, store: CredentialsStore) -> None:
        assert store.has_openai_credentials() is False
        assert store.get_openai_api_key() is None

    def test_store_and_retrieve(self, store: CredentialsStore) -> None:
        store.store_openai_api_key('oai-key')
        assert store.has_openai_credentials() is True
        assert store.get_openai_api_key() == 'oai-key'


class TestCredentialsStoreIsolation:
    def test_providers_do_not_interfere(self, store: CredentialsStore) -> None:
        store.store_google_api_key('ggl-key')
        assert store.has_strava_credentials() is False
        assert store.has_openai_credentials() is False

    def test_credentials_persist_across_instances(self, tmp_path: Path) -> None:
        CredentialsStore(config_dir=tmp_path).store_google_api_key('ggl-key')
        assert CredentialsStore(config_dir=tmp_path).get_google_api_key() == 'ggl-key'

    def test_credentials_file_permissions(self, tmp_path: Path) -> None:
        store = CredentialsStore(config_dir=tmp_path)
        store.store_google_api_key('key')
        file = tmp_path / 'credentials.json'
        assert oct(file.stat().st_mode)[-3:] == '600'
