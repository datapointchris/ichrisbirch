import logging
from typing import Annotated

import jwt
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.exceptions import ForbiddenException
from ichrisbirch.api.exceptions import UnauthorizedException
from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# CORE VALIDATION FUNCTIONS
# =============================================================================


def validate_user_email(email: str, session: Session) -> models.User | None:
    """Validate and retrieve user by email address."""
    query = select(models.User).where(models.User.email == email)
    if not (user := session.execute(query).scalars().first()):
        logger.warning(f'user with email {email} not found')
    return user


def validate_user_id(user_id: str, session: Session) -> models.User | None:
    """Validate and retrieve user by alternative ID."""
    query = select(models.User).where(models.User.alternative_id == int(user_id))
    if not (user := session.execute(query).scalars().first()):
        logger.warning(f'user with id {user_id} not found')
    return user


def validate_password(user: models.User, password: str) -> bool:
    """Validate user password."""
    if not user.check_password(password):
        logger.warning(f'incorrect password for user: {user.email}')
        return False
    return True


# =============================================================================
# JWT TOKEN UTILITIES
# =============================================================================


def get_token_from_header(authorization: Annotated[str | None, Header()] = None) -> str | None:
    """Extract Bearer token from Authorization header."""
    if authorization is None:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Authorization scheme must be Bearer')
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid authorization header format') from e


def validate_jwt_token(token: str, settings: Settings) -> str | None:
    """Validate a JWT token and return the user ID if valid.

    This is a pure function that can be called directly without FastAPI dependencies. Used by endpoints that need to validate tokens
    manually.
    """
    if not token:
        return None
    try:
        decoded_token = jwt.decode(jwt=token, key=settings.auth.jwt_secret_key, algorithms=[settings.auth.jwt_signing_algorithm])
        return decoded_token.get('sub')
    except jwt.ExpiredSignatureError:
        logger.debug('JWT token expired')
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f'JWT token validation error: {e}')
        return None


def get_token_handler(settings: Settings = Depends(get_settings), session: Session = Depends(get_sqlalchemy_session)) -> JWTTokenHandler:
    """Factory function for JWT token handler with dependencies."""
    return JWTTokenHandler(settings=settings, session=session)


# =============================================================================
# AUTHENTICATION METHODS (FastAPI Dependencies)
# =============================================================================


def authenticate_with_jwt(token: Annotated[str, Depends(get_token_from_header)], settings: Settings = Depends(get_settings)) -> str | None:
    """FastAPI dependency function for JWT authentication.

    Extracts token from Authorization header and validates it. Returns user ID if valid, None otherwise.
    """
    return validate_jwt_token(token, settings)


def authenticate_with_application_headers(
    x_application_id: str | None = Header(None),
    x_user_id: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """FastAPI dependency for application header authentication.

    Used by internal services that authenticate with X-Application-ID and X-User-ID headers.
    """
    if x_application_id and x_user_id:
        if x_application_id != settings.flask.app_id:
            logger.warning(f'invalid X-Application-ID header: {x_application_id[:-8]}')
            return None
        return x_user_id
    return None


def authenticate_with_internal_service_headers(
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """FastAPI dependency for internal service authentication.

    Used by internal services that authenticate with X-Internal-Service and X-Service-Key headers. Returns True if valid, False otherwise.
    """
    if x_internal_service and x_service_key:
        if x_service_key == settings.auth.internal_service_key:
            logger.debug(f'authenticated internal service: {x_internal_service}')
            return True
        else:
            logger.warning(f'invalid X-Service-Key for service: {x_internal_service}')
    return False


async def authenticate_with_oauth2(request: Request, session: Session = Depends(get_sqlalchemy_session)) -> str | None:
    """FastAPI dependency for OAuth2 form authentication.

    Validates username/password from form data. Returns user ID if valid, None otherwise.
    """
    form_data = await request.form()
    username = form_data.get('username')
    password = form_data.get('password')
    if not username or not password:
        return None

    user = validate_user_email(str(username), session)
    if not user or not validate_password(user, str(password)):
        return None

    return user.get_id()


# =============================================================================
# CURRENT USER DEPENDENCIES
# =============================================================================


def get_current_user(
    app_headers=Depends(authenticate_with_application_headers),
    auth_jwt=Depends(authenticate_with_jwt),
    auth_oauth2=Depends(authenticate_with_oauth2),
    session=Depends(get_sqlalchemy_session),
) -> models.User:
    """Main authentication dependency that tries multiple auth methods.

    Priority order:
    1. Application headers (internal services)
    2. JWT token (API clients)
    3. OAuth2 form data (web forms)

    Returns the authenticated user or raises UnauthorizedException.
    """
    if app_headers:
        logger.debug('using app headers for login')
    if auth_jwt:
        logger.debug('using jwt token for login')
    if auth_oauth2:
        logger.debug('using oauth form for login')

    if not (user_id := app_headers or auth_jwt or auth_oauth2):
        raise UnauthorizedException('Invalid credentials', logger)

    if not (user := validate_user_id(user_id, session)):
        raise UnauthorizedException('Invalid credentials', logger)

    logger.debug(f'validated credentials for user: {user.email}')
    return user


def get_admin_user(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    """Admin-only dependency that requires current user to be an admin.

    Returns the admin user or raises ForbiddenException.
    """
    if user.is_admin:
        return user
    raise ForbiddenException('Admin access required', logger)


def get_current_user_or_none(
    app_headers=Depends(authenticate_with_application_headers),
    auth_jwt=Depends(authenticate_with_jwt),
    auth_oauth2=Depends(authenticate_with_oauth2),
    session=Depends(get_sqlalchemy_session),
) -> models.User | None:
    """Same as get_current_user but returns None instead of raising exception.

    Used for dependencies that support multiple auth methods.
    """
    if not (user_id := app_headers or auth_jwt or auth_oauth2):
        return None

    if not (user := validate_user_id(user_id, session)):
        return None

    return user


def get_admin_or_internal_service_access(
    current_user: models.User | None = Depends(get_current_user_or_none),
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """Dependency that allows admin users OR internal services to access endpoints.

    Uses a non-throwing user dependency so we can check both auth methods.
    """
    # First check if this is an internal service request
    if x_internal_service and x_service_key:
        if x_service_key == settings.auth.internal_service_key:
            logger.debug(f'access granted for internal service: {x_internal_service}')
            return True
        else:
            logger.warning(f'invalid X-Service-Key for service: {x_internal_service}')

    # If not internal service, try admin user authentication
    if current_user:
        try:
            admin_user = get_admin_user(current_user)
            logger.debug(f'access granted for admin user: {admin_user.email}')
            return True
        except (UnauthorizedException, ForbiddenException) as exc:
            logger.debug(f'admin user auth failed: {exc}')

    # Neither internal service nor valid admin user
    raise UnauthorizedException('Admin or internal service access required', logger) from None


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[models.User, Depends(get_current_user)]
AdminUser = Annotated[models.User, Depends(get_admin_user)]
AdminOrInternalServiceAccess = Annotated[bool, Depends(get_admin_or_internal_service_access)]


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.post('/token/', response_model=None, status_code=status.HTTP_201_CREATED)
async def access_token(response: Response, user: CurrentUser, token_handler: JWTTokenHandler = Depends(get_token_handler)):
    """Create access and refresh tokens for authenticated user.

    Sets cookies and returns token data in response body.
    """
    access_token = token_handler.create_access_token(user.get_id())
    refresh_token = token_handler.create_refresh_token(user.get_id())
    token_handler.store_refresh_token(user.get_id(), refresh_token)

    response.set_cookie(key='access_token', value=f'Bearer {access_token}', httponly=True)
    response.set_cookie(key='refresh_token', value=refresh_token, httponly=True)

    return {'access_token': access_token, 'refresh_token': refresh_token}


@router.get('/token/validate/', status_code=status.HTTP_200_OK)
async def validate_token(
    jwt_token: Annotated[str, Depends(get_token_from_header)],
    access_token: str | None = Cookie(None),
    settings: Settings = Depends(get_settings),
):
    """Validate JWT token from header or cookie.

    Returns 200 if valid, raises UnauthorizedException if invalid.
    """
    logger.debug(f'token validation - header: {bool(jwt_token)}')
    logger.debug(f'token validation - cookie: {bool(access_token)}')
    token = jwt_token or access_token

    if not token:
        raise UnauthorizedException('Missing token', logger)

    if not validate_jwt_token(token, settings):
        raise UnauthorizedException('Invalid token', logger)

    return Response(status_code=status.HTTP_200_OK)


@router.post('/token/refresh/', status_code=status.HTTP_201_CREATED)
async def refresh_token(
    jwt_token: Annotated[str, Depends(get_token_from_header)],
    refresh_token: str = Cookie(None),
    token_handler: JWTTokenHandler = Depends(get_token_handler),
    settings: Settings = Depends(get_settings),
):
    """Refresh access token using valid refresh token.

    Validates the refresh token and creates a new access token.
    """
    logger.debug(f'token refresh - header: {bool(jwt_token)}')
    logger.debug(f'token refresh - cookie: {bool(refresh_token)}')
    refresh_token = jwt_token or refresh_token

    if not (user_id := validate_jwt_token(refresh_token, settings)):
        raise UnauthorizedException('Invalid refresh token', logger)

    logger.debug(f'refreshing token for user: {user_id}')
    if not token_handler.verify_refresh_token(user_id, refresh_token):
        raise UnauthorizedException('Invalid refresh token', logger)

    logger.debug(f'refresh token validated for user: {user_id}')
    new_access_token = token_handler.create_access_token(user_id)
    logger.debug(f'new access token created for user {user_id}: {new_access_token[-10:]}')

    response = JSONResponse(status_code=status.HTTP_201_CREATED, content={'access_token': new_access_token})
    response.set_cookie(key='access_token', value=f'Bearer {new_access_token}', httponly=True)
    return response


@router.get('/logout/', response_model=None, status_code=status.HTTP_200_OK)
async def logout_user(x_user_id: str = Header(...), token_handler: JWTTokenHandler = Depends(get_token_handler)):
    """Logout user by deleting their refresh token.

    Requires X-User-ID header for identification.
    """
    token_handler.delete_refresh_token(x_user_id)
    return Response(status_code=status.HTTP_200_OK)
