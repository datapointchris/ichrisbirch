from typing import Annotated

import structlog
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.client_scopes import permits
from ichrisbirch.api.client_scopes import reachable
from ichrisbirch.api.exceptions import ForbiddenException
from ichrisbirch.api.exceptions import Refusal
from ichrisbirch.api.exceptions import UnauthorizedException
from ichrisbirch.api.oidc_auth import UNAUTHORIZED_DETAIL
from ichrisbirch.api.oidc_auth import OIDCIdentity
from ichrisbirch.api.oidc_auth import ScopedClient
from ichrisbirch.api.oidc_auth import get_oidc_identity
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session

logger = structlog.get_logger()


# =============================================================================
# CORE VALIDATION FUNCTIONS
# =============================================================================


def validate_user_email(email: str, session: Session) -> models.User | None:
    """Validate and retrieve user by email address."""
    query = select(models.User).where(models.User.email == email)
    if not (user := session.execute(query).scalars().first()):
        logger.warning('user_not_found_by_email', email=email)
    return user


def validate_user_id(user_id: str, session: Session) -> models.User | None:
    """Validate and retrieve user by alternative ID."""
    query = select(models.User).where(models.User.alternative_id == int(user_id))
    if not (user := session.execute(query).scalars().first()):
        logger.warning('user_not_found_by_id', user_id=user_id)
    return user


# =============================================================================
# AUTHENTICATION METHODS (FastAPI Dependencies)
# =============================================================================


def get_scoped_client(
    identity: Annotated[OIDCIdentity | ScopedClient | None, Depends(get_oidc_identity)],
) -> ScopedClient | None:
    """The verified `icb-svc-` caller, or None for any other request."""
    return identity if isinstance(identity, ScopedClient) else None


def authenticate_with_oidc_bearer(
    identity: Annotated[OIDCIdentity | ScopedClient | None, Depends(get_oidc_identity)],
    session: Session = Depends(get_sqlalchemy_session),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """FastAPI dependency for the `icb` CLI's Authelia access token.

    `get_oidc_identity` has already verified the signature, issuer, expiry and client_id against
    Authelia's JWKS, or raised 401 — a token that reaches here is trusted. The access token carries
    no email, so the local user comes from settings rather than from the wire.

    A `ScopedClient` returns None here, and `refuse_scoped_client` answers it 403.

    Returns the user's alternative_id (as string) if valid, None otherwise.
    """
    if not isinstance(identity, OIDCIdentity):
        return None

    user = validate_user_email(settings.oidc.cli_user_email, session)
    if not user:
        # Returning None would drop a token that passed every cryptographic check into the weaker
        # strategies below, where a forged Remote-User header could still carry it.
        logger.error('oidc_cli_user_not_found', client_id=identity.client_id, email=settings.oidc.cli_user_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=UNAUTHORIZED_DETAIL)

    logger.debug('auth_method_oidc_bearer', client_id=identity.client_id, subject=identity.subject)
    return user.get_id()


def authenticate_with_authelia_headers(
    request: Request,
    session: Session = Depends(get_sqlalchemy_session),
) -> str | None:
    """FastAPI dependency for Authelia ForwardAuth header authentication.

    When Traefik's ForwardAuth validates a session with Authelia, it injects Remote-User
    and Remote-Email headers into the proxied request. This reads those headers and
    resolves to a local user.

    A request carrying an `Authorization` header is never read here. The edge sends any bearer
    request to ichrisbirch.com past ForwardAuth, so on such a request these headers came from the
    client. A token no other strategy accepts would otherwise fall through to them.

    Returns the user's alternative_id (as string) if valid, None otherwise.
    """
    remote_user = request.headers.get('Remote-User')
    remote_email = request.headers.get('Remote-Email')
    if 'Authorization' in request.headers:
        if remote_user or remote_email:
            logger.warning('authelia_headers_beside_authorization', remote_user=remote_user, remote_email=remote_email)
        return None
    if not remote_user or not remote_email:
        return None

    user = validate_user_email(remote_email, session)
    if not user:
        logger.warning('authelia_user_not_found', remote_user=remote_user, remote_email=remote_email)
        return None

    logger.debug('auth_method_authelia', remote_user=remote_user, email=user.email)
    return user.get_id()


def authenticate_with_application_headers(
    x_application_id: str | None = Header(None),
    x_user_id: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """FastAPI dependency for application header authentication.

    Used by internal services that authenticate with X-Application-ID, X-User-ID,
    and X-Service-Key headers. The service key is required to prevent impersonation.
    """
    if x_application_id and x_user_id and x_service_key:
        if x_service_key != settings.auth.internal_service_key:
            logger.warning('app_headers_invalid_service_key')
            return None
        if x_application_id != settings.app_id:
            logger.warning('app_headers_invalid_app_id', app_id=x_application_id[:-8])
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
            logger.debug('internal_service_authenticated', service=x_internal_service)
            return True
        else:
            logger.warning('internal_service_key_invalid', service=x_internal_service)
    return False


# =============================================================================
# CURRENT USER DEPENDENCIES
# =============================================================================


def authenticated_user(
    oidc_user_id=Depends(authenticate_with_oidc_bearer),
    authelia_user_id=Depends(authenticate_with_authelia_headers),
    app_headers=Depends(authenticate_with_application_headers),
    session=Depends(get_sqlalchemy_session),
) -> models.User | None:
    """The user the first matching strategy established, or None.

    FastAPI caches this per request, so a route whose router and `RequestZone` both ask for the
    caller looks the user up once.

    Priority order:
    0. Authelia OIDC access token (the `icb` CLI, verified in-process against Authelia's JWKS)
    1. Authelia ForwardAuth headers (browser SSO via Remote-User/Remote-Email)
    2. Application headers (internal services)
    """
    if oidc_user_id:
        logger.debug('auth_method_oidc_bearer')
    if authelia_user_id:
        logger.debug('auth_method_authelia')
    if app_headers:
        logger.debug('auth_method_app_headers')
    if not (user_id := oidc_user_id or authelia_user_id or app_headers):
        return None
    return validate_user_id(user_id, session)


def refuse_scoped_client(client: ScopedClient | None) -> None:
    """Raise 403 for a scoped client's token on a route that resolves a user.

    Without it, a request sending this token and a forged `Remote-User` header resolves through the
    header strategy and runs as that user.
    """
    if client is not None:
        logger.warning('scoped_client_outside_scopes', client_id=client.client_id)
        raise ForbiddenException(f'{Refusal.OUTSIDE_CLIENT_SCOPES}; {reachable(client.scopes)}', logger)


def get_current_user(
    client: Annotated[ScopedClient | None, Depends(get_scoped_client)],
    user: Annotated[models.User | None, Depends(authenticated_user)],
) -> models.User:
    """Main authentication dependency: the user any strategy established, or 401.

    A scoped client's token answers 403, because no scope lists a route that resolves a user.
    """
    refuse_scoped_client(client)

    if user is None:
        raise UnauthorizedException(Refusal.INVALID_CREDENTIALS, logger)

    logger.debug('credentials_validated', email=user.email)
    return user


def get_current_user_or_scoped_client(
    request: Request,
    client: Annotated[ScopedClient | None, Depends(get_scoped_client)],
    user: Annotated[models.User | None, Depends(authenticated_user)],
) -> models.User | ScopedClient:
    """`get_current_user` for a router with a route in `client_scopes.SCOPE_ROUTES`.

    A scoped client gets through only on a route that table lists for one of its scopes, and gets
    403 everywhere else. Every other caller resolves exactly as through `get_current_user`.
    """
    if client is not None and permits(client.scopes, request.method, request.scope.get('route')):
        logger.debug('auth_method_scoped_client', client_id=client.client_id, path=request.url.path)
        return client
    return get_current_user(client, user)


def get_admin_user(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    """Admin-only dependency that requires current user to be an admin.

    Returns the admin user or raises ForbiddenException.
    """
    if user.is_admin:
        return user
    raise ForbiddenException(Refusal.ADMIN_REQUIRED, logger)


def get_current_user_or_none(
    client: Annotated[ScopedClient | None, Depends(get_scoped_client)],
    user: Annotated[models.User | None, Depends(authenticated_user)],
) -> models.User | None:
    """Same as get_current_user but returns None instead of raising exception.

    Two cases still raise. `get_oidc_identity` rejects a presented-but-invalid access token before
    this runs, and `refuse_scoped_client` answers a scoped client's token 403. Without either, that
    token sent beside another strategy's credentials would be ignored, and the request would run as
    the user those credentials name.

    Used for dependencies that support multiple auth methods.
    """
    refuse_scoped_client(client)
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
            logger.debug('access_granted_internal_service', service=x_internal_service)
            return True
        else:
            logger.warning('internal_service_key_invalid', service=x_internal_service)

    # If not internal service, try admin user authentication
    if current_user:
        try:
            admin_user = get_admin_user(current_user)
            logger.debug('access_granted_admin_user', email=admin_user.email)
            return True
        except (UnauthorizedException, ForbiddenException) as exc:
            logger.debug('admin_auth_failed', error=str(exc))

    # Neither internal service nor valid admin user
    raise UnauthorizedException(Refusal.ADMIN_OR_INTERNAL_REQUIRED, logger) from None


# Type aliases for cleaner endpoint signatures
DbSession = Annotated[Session, Depends(get_sqlalchemy_session)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]
AdminUser = Annotated[models.User, Depends(get_admin_user)]
AdminOrInternalServiceAccess = Annotated[bool, Depends(get_admin_or_internal_service_access)]
