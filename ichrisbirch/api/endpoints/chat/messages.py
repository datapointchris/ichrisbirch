import logging
from typing import Annotated
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
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger('api.chat.messages')
router = APIRouter()


SQLAlchemySession = Annotated[Session, Depends(get_sqlalchemy_session)]


def IDNotFoundError(id: int | str):
    message = f'message {id} not found'
    logger.warning(message)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/', response_model=list[schemas.ChatMessage], status_code=status.HTTP_200_OK)
async def read_many(search: Optional[bool] = None, session: Session = Depends(get_sqlalchemy_session)):
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
    if event := session.get(models.ChatMessage, id):
        return event
    else:
        IDNotFoundError(id)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if chat := session.get(models.ChatMessage, id):
        session.delete(chat)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        IDNotFoundError(id)


@router.patch('/{id}/', response_model=schemas.ChatMessage, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ChatMessageUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: chat {id} {update_data}')
    if obj := session.get(models.ChatMessage, id):
        for attr, value in update_data.items():
            setattr(obj, attr, value)
        session.commit()
        session.refresh(obj)
        return obj
    else:
        IDNotFoundError(id)
