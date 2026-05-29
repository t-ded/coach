from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_PRIVACY_PAGE = Path(__file__).parent / 'static' / 'privacy.html'


@router.get('/legal/privacy')
def privacy_policy() -> FileResponse:
    return FileResponse(_PRIVACY_PAGE, media_type='text/html')
