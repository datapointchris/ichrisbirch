import structlog
from fastapi import APIRouter
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.Chat], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession, name: str | None = None):
    query = select(models.Chat).order_by(models.Chat.created_at.desc())
    if name is not None:
        query = query.where(models.Chat.name == name)
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Chat, status_code=status.HTTP_201_CREATED)
async def create(obj_in: schemas.ChatCreate, session: DbSession):
    messages = [models.ChatMessage(**m.model_dump()) for m in obj_in.messages]
    obj_in.messages = []
    obj = models.Chat(**obj_in.model_dump())
    obj.messages.extend(messages)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if chat := session.get(models.Chat, id):
        return chat
    raise NotFoundException('chat', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if chat := session.get(models.Chat, id):
        session.delete(chat)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('chat', id, logger)


@router.patch('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ChatUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('chat_update_patch', chat_id=id, update_data=update_data)

    if chat := session.get(models.Chat, id):
        for attr, value in update_data.items():
            setattr(chat, attr, value)
        session.commit()
        session.refresh(chat)
        return chat

    raise NotFoundException('chat', id, logger)


@router.put('/{id}/', response_model=schemas.Chat, status_code=status.HTTP_200_OK)
async def update_messages(id: int, update: schemas.ChatUpdate, session: DbSession):
    messages = [models.ChatMessage(**m.model_dump()) for m in update.messages]

    if chat := session.get(models.Chat, id):
        chat_message_ids = [message.id for message in chat.messages]
        logger.debug('chat_messages', chat_id=chat.id, message_ids=chat_message_ids)
        for message in messages:
            if (not message.chat_id) or (message.id not in chat_message_ids):
                message.chat_id = chat.id
                session.add(message)
                logger.debug('chat_message_added', message_id=message.id, chat_id=chat.id)
        session.commit()
        session.refresh(chat)
        logger.debug('chat_update_put', chat_id=id)
        return chat

    raise NotFoundException('chat', id, logger)
