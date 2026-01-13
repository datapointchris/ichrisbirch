from copy import deepcopy

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import AdminOrInternalServiceAccess
from ichrisbirch.api.endpoints.auth import CurrentUser
from ichrisbirch.api.endpoints.auth import get_admin_or_internal_service_access
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import get_current_user_or_none
from ichrisbirch.api.exceptions import ForbiddenException
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.api.exceptions import UnauthorizedException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session

logger = structlog.get_logger()
router = APIRouter()


def deep_merge(current_preferences, update):
    """Recursively merge nested dictionaries."""
    current = deepcopy(current_preferences)
    for key, value in update.items():
        if isinstance(value, dict) and key in current and isinstance(current[key], dict):
            current[key] = deep_merge(current[key], value)
        else:
            current[key] = value
    return current


def require_own_data_or_admin(
    current_user: models.User,
    target_user_id: int | None = None,
    target_alt_id: int | None = None,
    operation: str = 'access your own user data',
) -> None:
    """Ensure user can only access their own data unless they're admin."""
    is_accessing_own_data = (target_user_id is not None and current_user.id == target_user_id) or (
        target_alt_id is not None and current_user.alternative_id == target_alt_id
    )

    if not is_accessing_own_data and not current_user.is_admin:
        raise ForbiddenException(f'can only {operation}', logger)


async def require_admin_or_internal_service(
    access_granted: bool = Depends(get_admin_or_internal_service_access),
):
    """Custom dependency that allows admin users OR internal services."""
    return access_granted


@router.get('/', response_model=list[schemas.User], status_code=status.HTTP_200_OK)
async def read_many(
    session: Session = Depends(get_sqlalchemy_session), _: bool = Depends(require_admin_or_internal_service), limit: int | None = None
):
    """List all users.

    Requires admin user or internal service authentication.
    """
    query = select(models.User).limit(limit)
    return list(session.scalars(query).all())


async def require_user_access_or_admin_or_internal_service(
    id: int,
    current_user: models.User | None = Depends(get_current_user_or_none),
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """
    Custom dependency for user access:
    - Users can access their own data
    - Admin users can access any user data
    - Internal services can access any user data
    """
    # First check if this is an internal service request
    if x_internal_service and x_service_key:
        if x_service_key == settings.auth.internal_service_key:
            logger.debug(f'access granted for internal service: {x_internal_service}')
            return True
        else:
            logger.warning(f'invalid X-Service-Key for service: {x_internal_service}')

    # If not internal service, check user authentication
    if current_user:
        # Check if user can access this specific user data
        require_own_data_or_admin(current_user, target_user_id=id)
        return True

    # No valid authentication found
    raise UnauthorizedException('Authentication required', logger)


@router.get('/me/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def me(user: CurrentUser):
    """Get the current user using authentication methods for CurrentUser.

    NOTE: even though CurrentUser accepts oauth2 authentication, the form data
    cannot be POSTed to this endpoint.
    Instead the client must send the POST to /auth/token/ to obtain a token
    and then use the token for this endpoint.
    """
    return user


@router.get('/{id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_one(
    id: int,
    session: Session = Depends(get_sqlalchemy_session),
    _: bool = Depends(require_user_access_or_admin_or_internal_service),
):
    """Get user by ID.

    Users can access their own data. Admin users or internal services can access any user data.
    """
    if db_user := session.get(models.User, id):
        return db_user
    raise NotFoundException('user', id, logger)


@router.post('/', response_model=schemas.User, status_code=status.HTTP_201_CREATED, dependencies=None)
async def create(
    user: schemas.UserCreate,
    session: Session = Depends(get_sqlalchemy_session),
    settings: Settings = Depends(get_settings),
):
    if not settings.auth.accepting_new_signups:
        message = settings.auth.no_new_signups_message
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    db_obj = models.User(**user.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


async def _update_user_preferences_helper(db_user: models.User, update_data: dict, session: Session) -> models.User:
    """Helper function to update user preferences with error handling."""
    try:
        db_user.preferences = deep_merge(db_user.preferences, update_data)
    except ValueError as e:
        logger.error(f'failed to update preferences: {e}')
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f'unexpected error updating preferences: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='An unexpected error occurred') from e

    session.commit()
    session.refresh(db_user)
    return db_user


@router.patch('/me/preferences/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update_my_preferences(request: Request, user: CurrentUser, session: Session = Depends(get_sqlalchemy_session)):
    """Update the current user's preferences."""
    update_data = await request.json()
    logger.debug(f'update: user preferences {update_data}')

    # The session attached to the CurrentUser has gone out of scope, must re-attach to the new session
    db_user = session.merge(user)
    return await _update_user_preferences_helper(db_user, update_data, session)


@router.patch('/{id}/preferences/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update_user_preferences(
    id: int,
    request: Request,
    user: CurrentUser,
    session: Session = Depends(get_sqlalchemy_session),
):
    """Update a specific user's preferences.

    Users can only update their own preferences unless they are admin.
    """
    require_own_data_or_admin(user, target_user_id=id, operation='update your own preferences')

    update_data = await request.json()
    logger.debug(f'update: user {id} preferences {update_data}')

    if not (db_user := session.get(models.User, id)):
        raise NotFoundException('user', id, logger)

    return await _update_user_preferences_helper(db_user, update_data, session)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, admin_user: models.User = Depends(get_admin_user), session: Session = Depends(get_sqlalchemy_session)):
    """Delete a user (admin only).

    Admin users cannot delete themselves.
    """
    # Prevent self-deletion
    if admin_user.id == id:
        raise ForbiddenException('Cannot delete your own account', logger)

    if user := session.get(models.User, id):
        session.delete(user)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('user', id, logger)


async def require_update_access(
    id: int,
    current_user: models.User | None = Depends(get_current_user_or_none),
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """
    Custom dependency for user update access:
    - Users can update their own data
    - Admin users can update any user data
    - Internal services can update any user data
    """
    # First check if this is an internal service request
    if x_internal_service and x_service_key:
        if x_service_key == settings.auth.internal_service_key:
            logger.debug(f'access granted for internal service: {x_internal_service}')
            return True
        else:
            logger.warning(f'invalid X-Service-Key for service: {x_internal_service}')

    # If not internal service, check user authentication
    if current_user:
        # Check if user can update this specific user data
        require_own_data_or_admin(current_user, target_user_id=id, operation='update your own user data')
        return True

    # No valid authentication found
    raise UnauthorizedException('Authentication required', logger)


@router.patch('/{id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update(
    id: int,
    update: schemas.UserUpdate,
    session: Session = Depends(get_sqlalchemy_session),
    _: bool = Depends(require_update_access),
):
    """Update a user.

    Users can only update their own data unless they are admin or internal service.
    """
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: user {id} {update_data}')

    if db_user := session.get(models.User, id):
        for attr, value in update_data.items():
            setattr(db_user, attr, value)
        session.commit()
        session.refresh(db_user)
        return db_user

    raise NotFoundException('user', id, logger)


@router.get('/alt/{alternative_id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_by_alternative_id(
    alternative_id: int,
    session: Session = Depends(get_sqlalchemy_session),
    current_user: models.User | None = Depends(get_current_user_or_none),
    x_internal_service: str | None = Header(None),
    x_service_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
):
    """Get user by alternative ID.

    Users can only access their own data unless they are admin. Internal services can access any user.
    """
    query = select(models.User).where(models.User.alternative_id == alternative_id)
    if db_user := session.execute(query).scalars().first():
        # Check if this is an internal service request
        if x_internal_service and x_service_key:
            if x_service_key == settings.auth.internal_service_key:
                logger.debug(f'access granted for internal service: {x_internal_service}')
                return db_user
            else:
                logger.warning(f'invalid X-Service-Key for service: {x_internal_service}')
                raise UnauthorizedException('Invalid internal service credentials', logger)

        # If not internal service, require user authentication
        if current_user is None:
            raise UnauthorizedException('Authentication required', logger)

        require_own_data_or_admin(current_user, target_alt_id=alternative_id)
        return db_user

    raise NotFoundException('user with alternative_id', alternative_id, logger)


@router.get('/email/{email}/', response_model=schemas.User | None, status_code=status.HTTP_200_OK)
async def read_by_email(
    email: str,
    _: AdminOrInternalServiceAccess,
    session: Session = Depends(get_sqlalchemy_session),
):
    """Get user by email address.

    Requires internal service authentication.
    """
    query = select(models.User).where(models.User.email == email)
    if user := session.execute(query).scalars().first():
        return user
    raise NotFoundException('user with email', email, logger)
