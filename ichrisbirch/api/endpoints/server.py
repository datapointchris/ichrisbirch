import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.get("/", response_model=schemas.ServerStats, status_code=status.HTTP_200_OK)
def health():
    return schemas.ServerStats(
        name=settings.fastapi.title,
        environment=os.getenv('ENVIRONMENT', 'NOT SET'),
        api_url=os.getenv('API_URL', 'NOT SET'),
        log_level=os.getenv('LOG_LEVEL', 'NOT SET'),
        server_time=datetime.now().isoformat(),
        local_time=datetime.now(tz=ZoneInfo('America/Chicago')).isoformat(),
    )
