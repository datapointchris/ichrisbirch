import logging
import os
from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings

logger = logging.getLogger('api.server')

router = APIRouter()


@router.get("/", response_model=schemas.ServerStats, status_code=status.HTTP_200_OK)
def health(settings: Settings = Depends(get_settings)) -> schemas.ServerStats:
    return schemas.ServerStats(
        name=settings.fastapi.title,
        environment=os.getenv('ENVIRONMENT', 'NOT SET'),
        api_url=os.getenv('API_URL', 'NOT SET'),
        log_level=os.getenv('LOG_LEVEL', 'NOT SET'),
        server_time=datetime.now().isoformat(),
    )
