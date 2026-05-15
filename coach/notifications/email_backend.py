import resend

from coach.notifications.service import NotificationBackend


class ResendEmailBackend(NotificationBackend):
    def __init__(self, *, api_key: str, from_address: str) -> None:
        self._api_key = api_key
        self._from_address = from_address

    def send(self, *, to: str, subject: str, html_body: str) -> None:
        resend.api_key = self._api_key
        resend.Emails.send(
            {
                'from': self._from_address,
                'to': [to],
                'subject': subject,
                'html': html_body,
            },
        )
