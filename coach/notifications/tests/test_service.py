from coach.notifications.service import NotificationBackend
from coach.notifications.service import NotificationService


class FakeBackend(NotificationBackend):
    def __init__(self) -> None:
        self.last_call: dict[str, str] | None = None

    def send(self, *, to: str, subject: str, html_body: str) -> None:
        self.last_call = {'to': to, 'subject': subject, 'html_body': html_body}


class TestNotificationService:
    def setup_method(self) -> None:
        self._backend = FakeBackend()
        self._service = NotificationService(self._backend)

    def test_send_activity_insight_delivers_to_recipient(self) -> None:
        self._service.send_activity_insight(to='athlete@example.com', insight='Great run!')
        assert self._backend.last_call is not None
        assert self._backend.last_call['to'] == 'athlete@example.com'

    def test_send_activity_insight_includes_insight_in_body(self) -> None:
        self._service.send_activity_insight(to='athlete@example.com', insight='Solid tempo effort.')
        assert self._backend.last_call is not None
        assert 'Solid tempo effort.' in self._backend.last_call['html_body']

    def test_send_activity_insight_includes_app_link_in_body(self) -> None:
        self._service.send_activity_insight(to='athlete@example.com', insight='Nice effort.')
        assert self._backend.last_call is not None
        assert 'href=' in self._backend.last_call['html_body']

    def test_send_activity_insight_escapes_html_in_insight(self) -> None:
        self._service.send_activity_insight(to='athlete@example.com', insight='Watch out for <tags> & "quotes".')
        assert self._backend.last_call is not None
        body = self._backend.last_call['html_body']
        assert '<tags>' not in body
        assert '&lt;tags&gt;' in body
