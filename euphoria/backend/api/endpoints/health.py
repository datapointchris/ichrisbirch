from fastapi import APIRouter
from ...common import schemas
from euphoria import __version__
from datetime import datetime


router = APIRouter(prefix='/health', tags=['health'])


# TODO: It would be cool to have a test that ran after upgrading an api
# that hit this endpoint to make sure that the versions match so it got updated.
@router.get("/", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Root Get
    """
    return {
        "name": "Euphoria API",
        "version": __version__,
        "server_time": datetime.now().isoformat(),
    }
