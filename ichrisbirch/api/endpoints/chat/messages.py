import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


SQLAlchemySession = Annotated[Session, Depends(get_sqlalchemy_session)]


@router.get('/', response_model=list[schemas.ChatMessage], status_code=status.HTTP_200_OK)
async def read_many(search: bool | None = None, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.ChatMessage)
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.ChatMessage, status_code=status.HTTP_201_CREATED)
async def create(obj_in: schemas.ChatMessageCreate, session: Session = Depends(get_sqlalchemy_session)):
    obj = models.ChatMessage(**obj_in.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/{id}/', response_model=schemas.ChatMessage, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if message := session.get(models.ChatMessage, id):
        return message
    raise NotFoundException('message', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if message := session.get(models.ChatMessage, id):
        session.delete(message)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('message', id, logger)


@router.patch('/{id}/', response_model=schemas.ChatMessage, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ChatMessageUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: message {id} {update_data}')

    if message := session.get(models.ChatMessage, id):
        for attr, value in update_data.items():
            setattr(message, attr, value)
        session.commit()
        session.refresh(message)
        return message

    raise NotFoundException('message', id, logger)
