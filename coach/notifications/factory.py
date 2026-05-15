import os
from typing import Optional

from coach.notifications.email_backend import ResendEmailBackend
from coach.notifications.service import NotificationService

_RESEND_API_KEY_ENV = 'RESEND_API_KEY'
_RESEND_FROM_EMAIL_ENV = 'RESEND_FROM_EMAIL'


def build_notification_service() -> Optional[NotificationService]:
    api_key = os.environ.get(_RESEND_API_KEY_ENV)
    from_address = os.environ.get(_RESEND_FROM_EMAIL_ENV)
    if not api_key or not from_address:
        return None
    return NotificationService(ResendEmailBackend(api_key=api_key, from_address=from_address))
