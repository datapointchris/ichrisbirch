"""Internal service authentication for Flask-to-FastAPI communication."""

import logging

from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status

from ichrisbirch.config import settings

logger = logging.getLogger(__name__)


def verify_internal_service(
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
) -> bool:
    """Verify internal service authentication using service headers."""
    if not x_internal_service or not x_service_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Internal service authentication required')

    expected_key = getattr(settings.auth, 'internal_service_key', None)
    if not expected_key:
        logger.error('Internal service key not configured')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal authentication not configured')

    if x_service_key != expected_key:
        logger.warning(f'Invalid internal service key from {x_internal_service}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid service credentials')

    logger.debug(f'Authenticated internal service: {x_internal_service}')
    return True


# Dependency for endpoints that allow internal service access
InternalServiceAuth = Depends(verify_internal_service)
