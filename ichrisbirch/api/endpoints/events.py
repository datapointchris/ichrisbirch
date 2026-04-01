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


@router.get('/', response_model=list[schemas.Event], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession):
    query = select(models.Event).order_by(models.Event.date.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create(event: schemas.EventCreate, session: DbSession):
    logger.debug('event_create', date_from_app=str(event.date))
    db_obj = models.Event(**event.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.debug('event_created', date_from_db=str(db_obj.date))
    return db_obj


@router.get('/{id}/', response_model=schemas.Event, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if event := session.get(models.Event, id):
        return event
    raise NotFoundException('event', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if event := session.get(models.Event, id):
        session.delete(event)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('event', id, logger)


@router.patch('/{id}/', response_model=schemas.Event, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.EventUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('event_update', event_id=id, update_data=update_data)

    if event := session.get(models.Event, id):
        for attr, value in update_data.items():
            setattr(event, attr, value)
        session.commit()
        session.refresh(event)
        return event

    raise NotFoundException('event', id, logger)


@router.patch('/{id}/attend/', response_model=schemas.Event, status_code=status.HTTP_200_OK)
async def attend(id: int, session: DbSession):
    if event := session.get(models.Event, id):
        event.attending = True
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    raise NotFoundException('event', id, logger)
