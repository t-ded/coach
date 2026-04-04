import hashlib
import hmac
import json
import logging
import os
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from supabase import Client

from coach.auth.strava_tokens import SupabaseStravaTokenRepository
from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.deauthorize import deauthorize_athlete
from coach.ingestion.strava.mapper import map_strava_activity
from coach.persistence.database import create_secret_client
from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.repositories.users import SupabaseUsersRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_strava_signature(body: bytes, signature_header: str) -> bool:
    client_secret = os.environ.get('STRAVA_CLIENT_SECRET', '')
    expected = 'sha256=' + hmac.new(client_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _get_verify_token() -> str:
    token = os.environ.get('STRAVA_WEBHOOK_VERIFY_TOKEN')
    if not token:
        raise RuntimeError('STRAVA_WEBHOOK_VERIFY_TOKEN is not set')
    return token


@router.get('/webhook/strava')
def strava_webhook_challenge(request: Request) -> dict[str, str]:
    hub_challenge = request.query_params.get('hub.challenge', '')
    hub_verify_token = request.query_params.get('hub.verify_token', '')

    if hub_verify_token != _get_verify_token():
        raise HTTPException(status_code=403, detail='Invalid verify token')

    return {'hub.challenge': hub_challenge}


@router.post('/webhook/strava')
async def strava_webhook_event(
    request: Request,
    secret_client: Client = Depends(create_secret_client),  # noqa: B008
) -> dict[str, str]:
    body = await request.body()
    if not _verify_strava_signature(body, request.headers.get('X-Hub-Signature', '')):
        raise HTTPException(status_code=403, detail='Invalid webhook signature')

    payload: dict[str, Any] = json.loads(body)

    object_type = payload.get('object_type')
    aspect_type = payload.get('aspect_type')
    owner_id = payload.get('owner_id')
    object_id = payload.get('object_id')

    if object_type == 'athlete' and aspect_type == 'deauthorization' and owner_id is not None:
        deauthorize_athlete(int(owner_id), secret_client)
    elif object_type == 'activity' and aspect_type is not None and owner_id is not None and object_id is not None:
        _handle_activity_event(aspect_type, int(owner_id), int(object_id), secret_client)
    else:
        logger.debug('Ignoring unrecognised webhook event: object_type=%s aspect_type=%s', object_type, aspect_type)

    return {'status': 'ok'}


def _handle_activity_event(aspect_type: str, owner_id: int, object_id: int, secret_client: Client) -> None:
    user_id = SupabaseUsersRepository.find_user_id_by_strava_id(secret_client, owner_id)
    if user_id is None:
        logger.debug('Activity webhook for unknown Strava athlete %d — ignored.', owner_id)
        return

    activity_repo = SupabaseActivityRepository(secret_client, user_id)

    if aspect_type == 'delete':
        activity_repo.delete_by_strava_id(object_id)
        logger.info('Deleted activity %d for user %s via webhook.', object_id, user_id)
    elif aspect_type in ('create', 'update'):
        strava_client = StravaClient(user_id, SupabaseStravaTokenRepository(secret_client))
        raw = strava_client.get_detailed_activity(object_id)
        activity = map_strava_activity(raw)
        activity_repo.save(activity)
        logger.info('Upserted activity %d for user %s via webhook (%s).', object_id, user_id, aspect_type)
    else:
        logger.debug('Ignoring unrecognised activity aspect_type=%s for athlete %d.', aspect_type, owner_id)
