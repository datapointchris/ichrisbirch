from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

router = APIRouter(prefix='', tags=['home'], include_in_schema=False)


@router.get("/", include_in_schema=False, status_code=status.HTTP_200_OK)
async def docs_redirect():
    """Homepage of API"""
    # return {'message': 'This is the home page, no redirction'}
    return RedirectResponse(url='/docs')
