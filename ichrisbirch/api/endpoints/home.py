from fastapi import APIRouter
from fastapi import status
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/", include_in_schema=False, status_code=status.HTTP_200_OK)
async def docs_redirect():
    """Homepage of API"""
    # return {'message': 'This is the home page, no redirction'}
    return RedirectResponse(url='/docs')
