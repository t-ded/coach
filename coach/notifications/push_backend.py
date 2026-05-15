from coach.notifications.service import NotificationBackend


class PushBackend(NotificationBackend):
    def send(self, *, to: str, subject: str, html_body: str) -> None:
        raise NotImplementedError('Push notifications not yet implemented')
