from fastapi import APIRouter
from fastapi import status
from fastapi.responses import RedirectResponse

from ichrisbirch.api import API_PREFIX

router = APIRouter()


@router.get('/', include_in_schema=False, status_code=status.HTTP_200_OK)
def docs_redirect():
    """Homepage of API."""
    return RedirectResponse(url=f'{API_PREFIX}/docs')


@router.get('/health', include_in_schema=False, status_code=status.HTTP_200_OK)
def health():
    """Health check endpoint for container health monitoring."""
    return {'status': 'ok'}
