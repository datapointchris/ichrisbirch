import logging
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

# from ..dependencies import auth
from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[schemas.User], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(sqlalchemy_session), limit: Optional[int] = None):
    query = select(models.User).limit(limit)
    return list(session.scalars(query).all())


@router.get('/me/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def me(user_id: int, session: Session = Depends(sqlalchemy_session)):
    if user := session.get(models.User, user_id):
        return user
    else:
        message = f'User {user_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.post('/', response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create(user: schemas.UserCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.User(**user.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{user_id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_one(user_id: int, alt: bool = False, session: Session = Depends(sqlalchemy_session)):
    if user := session.get(models.User, user_id):
        return user
    else:
        message = f'User {user_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{user_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(user_id: int, session: Session = Depends(sqlalchemy_session)):
    if user := session.get(models.User, user_id):
        session.delete(user)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'User {user_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/alt/{alternative_id}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_by_alternative_id(alternative_id: int, session: Session = Depends(sqlalchemy_session)):
    query = select(models.User).where(models.User.alternative_id == alternative_id)
    if result := session.scalars(query).first():
        return result
    else:
        message = f'User with alternative_id {alternative_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/email/{email}/', response_model=schemas.User, status_code=status.HTTP_200_OK)
async def read_by_email(email: str, session: Session = Depends(sqlalchemy_session)):
    query = select(models.User).where(models.User.email == email)
    result = session.execute(query).scalars().first()
    if result:
        return result
    else:
        message = f'User with email {email} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
