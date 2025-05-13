import logging
from copy import deepcopy
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import CurrentUser
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger('api.users')
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


@router.get(
    "/", response_model=list[schemas.User], status_code=status.HTTP_200_OK, dependencies=[Depends(get_admin_user)]
)
async def read_many(session: Session = Depends(get_sqlalchemy_session), limit: Optional[int] = None):
    query = select(models.User).limit(limit)
    return list(session.scalars(query).all())


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


@router.get('/me/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def me(user: CurrentUser):
    """Get the current user using authentication methods for CurrentUser.

    NOTE: even though CurrentUser accepts oauth2 authentication, the form data
    cannot be POSTed to this endpoint.
    Instead the client must send the POST to /auth/token/ to obtain a token
    and then use the token for this endpoint.
    """
    return user


@router.patch('/me/preferences/', response_model=schemas.User, status_code=status.HTTP_200_OK)
@router.patch('/{id}/preferences/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update_preferences(user: CurrentUser, update: dict, session: Session = Depends(get_sqlalchemy_session)):
    logger.debug(f'update: user preferences {update}')
    # The session attached to the CurrentUser has gone out of scope, must re-attach to the new session
    db_user = session.merge(user)
    try:
        db_user.preferences = deep_merge(db_user.preferences, update)
    except ValueError as e:
        logger.error(f'failed to update preferences: {e}')
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f'unexpected error updating preferences: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get('/{id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if user := session.get(models.User, id):
        return user
    raise NotFoundException("user", id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if user := session.get(models.User, id):
        session.delete(user)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException("user", id, logger)


@router.patch('/{id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.UserUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: user {id} {update_data}')

    if user := session.get(models.User, id):
        for attr, value in update_data.items():
            setattr(user, attr, value)
        session.commit()
        session.refresh(user)
        return user

    raise NotFoundException("user", id, logger)


@router.get('/alt/{alternative_id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_by_alternative_id(alternative_id: int, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.User).where(models.User.alternative_id == alternative_id)
    if user := session.scalars(query).first():
        return user
    raise NotFoundException("user with alternative_id", alternative_id, logger)


@router.get('/email/{email}/', response_model=Optional[schemas.User], status_code=status.HTTP_200_OK)
async def read_by_email(email: str, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.User).where(models.User.email == email)
    if user := session.execute(query).scalars().first():
        return user
    raise NotFoundException("user with email", email, logger)
