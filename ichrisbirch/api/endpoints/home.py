from fastapi import APIRouter
from fastapi import status
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get('/', include_in_schema=False, status_code=status.HTTP_200_OK)
def docs_redirect():
    """Homepage of API."""
    # return {'message': 'This is the home page, no redirction'}
    return RedirectResponse(url='/docs')


@router.get('/health', include_in_schema=False, status_code=status.HTTP_200_OK)
def health():
    """Health check endpoint for container health monitoring."""
    return {'status': 'healthy'}
