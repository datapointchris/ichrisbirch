import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models, schemas
from ichrisbirch.config import get_settings
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

settings = get_settings()
router = APIRouter(prefix='/countdowns', tags=['countdowns'], responses=settings.fastapi.responses)
logger = logging.getLogger(__name__)


@router.get('/', response_model=list[schemas.Countdown])
async def read_many(session: Session = Depends(sqlalchemy_session)):
    """API method to read many countdowns."""
    query = select(models.Countdown).order_by(models.Countdown.due_date.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Countdown, status_code=status.HTTP_201_CREATED)
async def create(countdown: schemas.CountdownCreate, session: Session = Depends(sqlalchemy_session)):
    """API method to create a new countdown."""
    db_obj = models.Countdown(**countdown.dict())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.Countdown)
async def read_one(id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to read one countdown."""
    if countdown := session.get(models.Countdown, id):
        return countdown
    else:
        message = f'Countdown {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{id}/', status_code=200)
async def delete(id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to delete a countdown."""
    if countdown := session.get(models.Countdown, id):
        session.delete(countdown)
        session.commit()
        return countdown
    else:
        message = f'Countdown {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
