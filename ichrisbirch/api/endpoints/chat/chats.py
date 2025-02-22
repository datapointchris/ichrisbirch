import logging
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

logger = logging.getLogger('api.chat')
router = APIRouter()


def IDNotFoundError(id: int | str):
    message = f'chat {id} not found'
    logger.warning(message)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/', response_model=list[schemas.Chat], status_code=status.HTTP_200_OK)
async def read_many(search: Optional[bool] = None, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.Chat)

    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Chat, status_code=status.HTTP_201_CREATED)
async def create(obj_in: schemas.ChatCreate, session: Session = Depends(get_sqlalchemy_session)):
    messages = [models.ChatMessage(**m.model_dump()) for m in obj_in.messages]
    obj_in.messages = []
    obj = models.Chat(**obj_in.model_dump())
    obj.messages.extend(messages)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/{name}/', response_model=schemas.Chat | None, status_code=status.HTTP_200_OK)
async def check_chat_exists_by_name(name: str, session: Session = Depends(get_sqlalchemy_session)):
    if not name:
        return None
    return session.scalars(select(models.Chat).where(models.Chat.name == name)).first()


@router.get('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if event := session.get(models.Chat, id):
        return event
    else:
        IDNotFoundError(id)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if chat := session.get(models.Chat, id):
        session.delete(chat)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        IDNotFoundError(id)


@router.patch('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ChatUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update by PATCH: chat {id} {update_data}')
    if obj := session.get(models.Chat, id):
        for attr, value in update_data.items():
            setattr(obj, attr, value)
        session.commit()
        session.refresh(obj)
        return obj
    else:
        IDNotFoundError(id)


@router.put('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def update_messages(id: int, update: schemas.ChatUpdate, session: Session = Depends(get_sqlalchemy_session)):
    messages = [models.ChatMessage(**m.model_dump()) for m in update.messages]
    if chat := session.get(models.Chat, id):
        chat_message_ids = [message.id for message in chat.messages]
        logger.debug(f'{chat.id} has message ids: {chat_message_ids}')
        for message in messages:
            if (not message.chat_id) or (message.id not in chat_message_ids):
                message.chat_id = chat.id
                session.add(message)
                logger.warning(f'Added message {message.id}: {message.content[:20]} to chat {chat.id}')
        session.commit()
        session.refresh(chat)
        logger.debug(f'update by PUT: chat {id}')
        return chat
    else:
        IDNotFoundError(id)
