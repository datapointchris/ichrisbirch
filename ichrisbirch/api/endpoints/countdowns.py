import logging

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


@router.get('/', response_model=list[schemas.Countdown], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.Countdown).order_by(models.Countdown.due_date.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Countdown, status_code=status.HTTP_201_CREATED)
async def create(countdown: schemas.CountdownCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.Countdown(**countdown.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.Countdown, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if countdown := session.get(models.Countdown, id):
        return countdown
    raise NotFoundException('countdown', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if countdown := session.get(models.Countdown, id):
        session.delete(countdown)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('countdown', id, logger)


@router.patch('/{id}/', response_model=schemas.Countdown, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.CountdownUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: countdown {id} {update_data}')

    if countdown := session.get(models.Countdown, id):
        for attr, value in update_data.items():
            setattr(countdown, attr, value)
        session.commit()
        session.refresh(countdown)
        return countdown

    raise NotFoundException('countdown', id, logger)
