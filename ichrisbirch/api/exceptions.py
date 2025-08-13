import logging

from fastapi import HTTPException
from fastapi import status


class NotFoundException(HTTPException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str | int, logger: logging.Logger):
        message = f'{resource_type} {resource_id} not found'
        logger.warning(message)
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class UnauthorizedException(HTTPException):
    """Exception raised when authentication fails or access is unauthorized."""

    def __init__(self, reason: str, logger: logging.Logger):
        message = f'Unauthorized: {reason}'
        logger.warning(message)
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


class ForbiddenException(HTTPException):
    """Exception raised when access to a resource is forbidden."""

    def __init__(self, reason: str, logger: logging.Logger):
        message = f'Access denied: {reason}'
        logger.warning(message)
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)
