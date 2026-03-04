from datetime import datetime

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import CurrentUser
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.models.personal_api_key import generate_api_key
from ichrisbirch.models.personal_api_key import hash_api_key

logger = structlog.get_logger()
router = APIRouter()


@router.post('/', response_model=schemas.PersonalAPIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create(
    data: schemas.PersonalAPIKeyCreate,
    user: CurrentUser,
    session: Session = Depends(get_sqlalchemy_session),
):
    raw_key = generate_api_key()
    db_obj = models.PersonalAPIKey(
        user_id=user.id,
        name=data.name,
        key_prefix=raw_key[:8],
        hashed_key=hash_api_key(raw_key),
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.info('personal_api_key_created', key_id=db_obj.id, user_id=user.id, name=data.name)
    return schemas.PersonalAPIKeyCreated(
        id=db_obj.id,
        name=db_obj.name,
        key_prefix=db_obj.key_prefix,
        created_at=db_obj.created_at,
        last_used_at=db_obj.last_used_at,
        revoked_at=db_obj.revoked_at,
        key=raw_key,
    )


@router.get('/', response_model=list[schemas.PersonalAPIKey], status_code=status.HTTP_200_OK)
async def read_many(user: CurrentUser, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.PersonalAPIKey).where(models.PersonalAPIKey.user_id == user.id).order_by(models.PersonalAPIKey.created_at.desc())
    return list(session.scalars(query).all())


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def revoke(id: int, user: CurrentUser, session: Session = Depends(get_sqlalchemy_session)):
    if key := session.get(models.PersonalAPIKey, id):
        if key.user_id != user.id:
            raise NotFoundException('api_key', id, logger)
        key.revoked_at = datetime.now()
        session.commit()
        logger.info('personal_api_key_revoked', key_id=id, user_id=user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('api_key', id, logger)
