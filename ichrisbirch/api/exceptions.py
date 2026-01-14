from typing import Any

from fastapi import HTTPException
from fastapi import status


class NotFoundException(HTTPException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str | int, logger: Any):
        logger.warning('resource_not_found', resource_type=resource_type, resource_id=resource_id)
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'{resource_type} {resource_id} not found')


class UnauthorizedException(HTTPException):
    """Exception raised when authentication fails or access is unauthorized."""

    def __init__(self, reason: str, logger: Any):
        logger.warning('unauthorized', reason=reason)
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Unauthorized: {reason}')


class ForbiddenException(HTTPException):
    """Exception raised when access to a resource is forbidden."""

    def __init__(self, reason: str, logger: Any):
        logger.warning('access_denied', reason=reason)
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=f'Access denied: {reason}')
