import enum
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from fastapi import status


class Refusal(enum.StrEnum):
    """The reasons this API refuses a request, as keys rather than sentences.

    A test asserting the sentence pins the wording, so rephrasing a refusal
    breaks tests that were never about the words. Naming the member and keeping
    the wording here means one edit moves both.

    A refusal carrying a value the caller supplied is not a member — it cannot
    be, since the text differs per call. Assert the interpolated value beside a
    stable condition instead, the way the `can only {operation}` refusal in
    `endpoints/users.py` is tested.
    """

    ADMIN_REQUIRED = 'Admin access required'
    ADMIN_OR_INTERNAL_REQUIRED = 'Admin or internal service access required'
    AUTH_REQUIRED = 'Authentication required'
    CANNOT_DELETE_OWN_ACCOUNT = 'Cannot delete your own account'
    INVALID_CREDENTIALS = 'Invalid credentials'
    INVALID_INTERNAL_CREDENTIALS = 'Invalid internal service credentials'
    INVALID_REFRESH_TOKEN = 'Invalid refresh token'
    INVALID_TOKEN = 'Invalid token'
    MISSING_TOKEN = 'Missing token'


class NotFoundException(HTTPException):
    """Exception raised when a requested resource is not found.

    `resource_type` is the noun a person reads, so it is written as words:
    'project item', not 'project_item'. The detail reaches a caller who is
    stuck — the `icb` CLI prints it verbatim, and the Vue app surfaces it — and
    an internal spelling there names something they cannot look up or type.
    """

    def __init__(self, resource_type: str, resource_id: str | int | UUID, logger: Any):
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


class FailedDependencyException(HTTPException):
    """A service this API called failed, so the request could not be finished.

    The detail names what failed: a site that could not be read, GitHub, or a
    reply from Claude Code that could not be used. The status is 424 rather than
    502 because Cloudflare sits in front of production. It replaces an origin's
    502 or 504 with its own error page, which drops the detail, and it passes a
    4xx through untouched.
    """

    def __init__(self, detail: Any):
        super().__init__(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=detail)
