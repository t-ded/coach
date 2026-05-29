from fastapi import FastAPI
from fastapi.testclient import TestClient

from coach.web.legal import router


class TestPrivacyPolicyPage:
    def setup_method(self) -> None:
        app = FastAPI()
        app.include_router(router)
        self._client = TestClient(app)
        self._response = self._client.get('/legal/privacy')

    def test_serves_html_page(self) -> None:
        assert self._response.status_code == 200
        assert 'text/html' in self._response.headers['content-type']

    def test_page_titled_privacy_policy(self) -> None:
        assert 'Privacy Policy' in self._response.text

    def test_explains_strava_data_deletion_on_disconnect(self) -> None:
        assert 'deauthorization' in self._response.text.lower()

    def test_states_data_is_used_for_inference_not_training(self) -> None:
        body = self._response.text.lower()
        assert 'inference' in body
        assert 'never to train' in body
