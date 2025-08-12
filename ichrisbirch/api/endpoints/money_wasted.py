import logging

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

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/', response_model=list[schemas.MoneyWasted], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.MoneyWasted).order_by(models.MoneyWasted.date_wasted.desc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.MoneyWasted, status_code=status.HTTP_201_CREATED)
async def create(countdown: schemas.MoneyWastedCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.MoneyWasted(**countdown.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.MoneyWasted, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if countdown := session.get(models.MoneyWasted, id):
        return countdown
    else:
        message = f'MoneyWasted {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if countdown := session.get(models.MoneyWasted, id):
        session.delete(countdown)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'MoneyWasted {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
