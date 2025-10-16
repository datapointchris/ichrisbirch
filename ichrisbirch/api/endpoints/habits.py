import datetime as dt
import logging

import pendulum
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/', response_model=schemas.Habit, status_code=status.HTTP_201_CREATED)
async def create_habit(habit: schemas.HabitCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.Habit(**habit.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/', response_model=list[schemas.Habit], status_code=status.HTTP_200_OK)
async def read_many_habits(session: Session = Depends(get_sqlalchemy_session), current: bool | None = None, limit: int | None = None):
    query = select(models.Habit).limit(limit)
    if current is True:
        query = query.filter(models.Habit.is_current.is_(True))
    if current is False:
        query = query.filter(models.Habit.is_current.is_(False))
    return list(session.scalars(query).all())


@router.post('/categories/', response_model=schemas.HabitCategory, status_code=status.HTTP_201_CREATED)
async def create_category(category: schemas.HabitCategoryCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.HabitCategory(**category.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/categories/', response_model=list[schemas.HabitCategory], status_code=status.HTTP_200_OK)
async def read_many_categories(session: Session = Depends(get_sqlalchemy_session), current: bool | None = None, limit: int | None = None):
    query = select(models.HabitCategory).limit(limit)
    if current is True:
        query = query.filter(models.HabitCategory.is_current.is_(True))
    if current is False:
        query = query.filter(models.HabitCategory.is_current.is_(False))
    return list(session.scalars(query).all())


@router.post('/completed/', response_model=schemas.HabitCompleted, status_code=status.HTTP_201_CREATED)
async def create_completed(habit: schemas.HabitCompletedCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.HabitCompleted(**habit.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/completed/', response_model=list[schemas.HabitCompleted], status_code=status.HTTP_200_OK)
async def read_many_completed(
    session: Session = Depends(get_sqlalchemy_session),
    start_date: dt.datetime | dt.date | str | None = None,
    end_date: dt.datetime | dt.date | str | None = None,
    first: bool | None = None,
    last: bool | None = None,
):
    query = select(models.HabitCompleted)

    if first:  # first completed
        query = query.order_by(models.HabitCompleted.complete_date.asc()).limit(1)

    elif last:  # most recent (last) completed
        query = query.order_by(models.HabitCompleted.complete_date.desc()).limit(1)

    elif start_date is None or end_date is None:  # return all if no start or end date
        query = query.order_by(models.HabitCompleted.complete_date.desc())

    else:  # filtered by start and end date
        query = query.filter(
            models.HabitCompleted.complete_date >= pendulum.parse(str(start_date)),
            models.HabitCompleted.complete_date <= pendulum.parse(str(end_date)),
        )
        query = query.order_by(models.HabitCompleted.complete_date.desc())

    return list(session.scalars(query).all())


@router.get('/{id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.Habit, id):
        return habit
    raise NotFoundException('habit', id, logger)


@router.patch('/{id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.HabitUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug(f'update: habit {id} {update_data}')

    if habit := session.get(models.Habit, id):
        for attr, value in update_data.items():
            setattr(habit, attr, value)
        session.commit()
        session.refresh(habit)
        return habit

    raise NotFoundException('habit', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.Habit, id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('habit', id, logger)


@router.get('/categories/{category_id}/', response_model=schemas.HabitCategory, status_code=status.HTTP_200_OK)
async def read_one_category(category_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if category := session.get(models.HabitCategory, category_id):
        return category
    raise NotFoundException('habit category', category_id, logger)


@router.patch('/categories/{category_id}/', response_model=schemas.HabitCategory, status_code=status.HTTP_200_OK)
async def update_habit_category(
    category_id: int, category_update: schemas.HabitCategoryUpdate, session: Session = Depends(get_sqlalchemy_session)
):
    if category := session.get(models.HabitCategory, category_id):
        for attr, value in category_update.model_dump().items():
            if value is not None:
                setattr(category, attr, value)
        session.commit()
        session.refresh(category)
        return category

    raise NotFoundException('habit category', category_id, logger)


@router.delete('/categories/{category_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if category := session.get(models.HabitCategory, category_id):
        try:
            session.delete(category)
            session.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            message = f"Habit category '{category.name}' cannot be deleted because it is in use"
            logger.warning(message)
            logger.warning(str(e).split('\n')[0])
            return Response(message, status_code=status.HTTP_409_CONFLICT)

    raise NotFoundException('habit category', category_id, logger)


@router.get('/completed/{completed_id}/', response_model=schemas.HabitCompleted, status_code=status.HTTP_200_OK)
async def read_one_completed(completed_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if completed := session.get(models.HabitCompleted, completed_id):
        return completed
    raise NotFoundException('habit completed', completed_id, logger)


@router.delete('/completed/{completed_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_completed(completed_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if completed := session.get(models.HabitCompleted, completed_id):
        session.delete(completed)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('habit completed', completed_id, logger)
