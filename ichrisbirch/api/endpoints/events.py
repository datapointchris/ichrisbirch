import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models, schemas
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/', response_model=list[schemas.Event], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(sqlalchemy_session)):
    query = select(models.Event).order_by(models.Event.date.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create(event: schemas.EventCreate, session: Session = Depends(sqlalchemy_session)):
    logger.debug(f'event date from app: {event.date}')
    db_obj = models.Event(**event.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.debug(f'event date from db: {db_obj.date}')
    return db_obj


@router.get('/{id}/', response_model=schemas.Event, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(sqlalchemy_session)):
    if event := session.get(models.Event, id):
        return event
    else:
        message = f'Event {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(sqlalchemy_session)):
    if event := session.get(models.Event, id):
        session.delete(event)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Event {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.post('/{id}/attend/', response_model=schemas.Event, status_code=status.HTTP_200_OK)
async def complete(id: int, session: Session = Depends(sqlalchemy_session)):
    if event := session.get(models.Event, id):
        event.attending = True
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    else:
        message = f'Event {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
