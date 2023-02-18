from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix='', tags=['main'], include_in_schema=False)


@router.get("/", include_in_schema=False)
async def docs_redirect():
    """Homepage of API"""
    # return {'message': 'This is the home page, no redirction'}
    return RedirectResponse(url='/docs')
