"""Internal service authentication for Flask-to-FastAPI communication."""

import structlog
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings

logger = structlog.get_logger()


def verify_internal_service(
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """Verify internal service authentication using service headers."""
    if not x_internal_service or not x_service_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Internal service authentication required')

    expected_key = settings.auth.internal_service_key
    if not expected_key:
        logger.error('internal_service_key_not_configured')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal authentication not configured')

    if x_service_key != expected_key:
        logger.warning('internal_service_key_invalid', service=x_internal_service)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid service credentials')

    logger.debug('internal_service_authenticated', service=x_internal_service)
    return True


# Dependency for endpoints that allow internal service access
InternalServiceAuth = Depends(verify_internal_service)
