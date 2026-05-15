import html as html_module
import os
from abc import ABC
from abc import abstractmethod


class NotificationBackend(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, html_body: str) -> None: ...


class NotificationService:
    _APP_URL_DEFAULT = 'http://localhost:8000'

    def __init__(self, backend: NotificationBackend) -> None:
        self._backend = backend
        self._app_url = os.environ.get('CHAINLIT_URL', self._APP_URL_DEFAULT)

    def send_activity_insight(self, *, to: str, insight: str) -> None:
        subject = 'Your latest activity — a note from Coach'
        html_body = self._render_html(insight)
        self._backend.send(to=to, subject=subject, html_body=html_body)

    def _render_html(self, insight: str) -> str:
        escaped = html_module.escape(insight).replace('\n', '<br>')
        app_url = html_module.escape(self._app_url)
        return f"""<!DOCTYPE html>
<html lang="en">
<body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1a1a1a;">
  <h2 style="font-size: 1.1rem; margin-bottom: 1rem; color: #333;">Post-activity note from Coach</h2>
  <p style="line-height: 1.6;">{escaped}</p>
  <p style="margin-top: 1.5rem;">
    <a href="{app_url}" style="background: #2563eb; color: white; padding: 0.6rem 1.2rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem;">Continue in Coach →</a>
  </p>
  <hr style="margin-top: 2rem; border: none; border-top: 1px solid #eee;">
  <p style="font-size: 0.75rem; color: #999; margin-top: 1rem;">
    You're receiving this because activity notifications are enabled in Coach.
    Open <a href="{app_url}" style="color: #999;">Coach</a> to manage your notification settings.
  </p>
</body>
</html>"""
