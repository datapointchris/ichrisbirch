from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from ichrisbirch.config import get_settings

settings = get_settings()

router = APIRouter(prefix='', tags=['home'], include_in_schema=False, responses=settings.fastapi.responses)


@router.get("/", include_in_schema=False)
async def docs_redirect():
    """Homepage of API"""
    # return {'message': 'This is the home page, no redirction'}
    return RedirectResponse(url='/docs')
