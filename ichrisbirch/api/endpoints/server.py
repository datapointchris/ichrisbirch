import logging
import os
from datetime import datetime

from fastapi import APIRouter
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.config import settings

logger = logging.getLogger('api.server')

router = APIRouter()


@router.get("/", response_model=schemas.ServerStats, status_code=status.HTTP_200_OK)
def health():
    return schemas.ServerStats(
        name=settings.fastapi.title,
        environment=os.getenv('ENVIRONMENT', 'NOT SET'),
        api_url=os.getenv('API_URL', 'NOT SET'),
        log_level=os.getenv('LOG_LEVEL', 'NOT SET'),
        server_time=datetime.now().isoformat(),
    )
