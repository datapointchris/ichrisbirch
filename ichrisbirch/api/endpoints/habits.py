import logging
from datetime import datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# from ..dependencies import auth
from ichrisbirch import models, schemas
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/', response_model=schemas.Habit, status_code=status.HTTP_201_CREATED)
async def create_habit(habit: schemas.HabitCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.Habit(**habit.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/", response_model=list[schemas.Habit], status_code=status.HTTP_200_OK)
async def read_many_habits(
    session: Session = Depends(sqlalchemy_session), current: Optional[bool] = None, limit: Optional[int] = None
):
    query = select(models.Habit).limit(limit)
    if current:
        query = query.filter(models.Habit.is_current.is_(True))
    return list(session.scalars(query).all())


@router.post('/categories/', response_model=schemas.HabitCategory, status_code=status.HTTP_201_CREATED)
async def create_category(category: schemas.HabitCategoryCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.HabitCategory(**category.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/categories/", response_model=list[schemas.HabitCategory], status_code=status.HTTP_200_OK)
async def read_many_categories(
    session: Session = Depends(sqlalchemy_session), current: Optional[bool] = None, limit: Optional[int] = None
):
    query = select(models.HabitCategory).limit(limit)
    if current:
        query = query.filter(models.HabitCategory.is_current.is_(True))
    return list(session.scalars(query).all())


@router.post('/completed/', response_model=schemas.HabitCompleted, status_code=status.HTTP_201_CREATED)
async def create_completed(habit: schemas.HabitCompletedCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.HabitCompleted(**habit.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/completed/", response_model=list[schemas.HabitCompleted], status_code=status.HTTP_200_OK)
async def read_many_completed(
    session: Session = Depends(sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
):
    logger.debug(f'Parameters passed: {start_date=}, {end_date=}, {first=}, {last=}')
    query = select(models.HabitCompleted)

    if first:  # first completed
        query = query.order_by(models.HabitCompleted.complete_date.asc()).limit(1)

    elif last:  # most recent (last) completed
        query = query.order_by(models.HabitCompleted.complete_date.desc()).limit(1)

    elif start_date is None or end_date is None:  # return all if no start or end date
        query = query.order_by(models.HabitCompleted.complete_date.desc())

    else:  # filtered by start and end date
        query = query.filter(
            models.HabitCompleted.complete_date >= start_date, models.HabitCompleted.complete_date <= end_date
        )
        query = query.order_by(models.HabitCompleted.complete_date.desc())

    return list(session.scalars(query).all())


@router.get('/{habit_id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def read_one_habit(habit_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.Habit, habit_id):
        return habit
    else:
        message = f'Habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{habit_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.Habit, habit_id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.post('/complete/{habit_id}/', response_model=schemas.HabitCompleted, status_code=status.HTTP_200_OK)
async def complete_habit(habit_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.Habit, habit_id):
        complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()  # type: ignore
        completed_habit = models.HabitCompleted(
            name=habit.name, category_id=habit.category_id, complete_date=complete_date
        )
        session.add(completed_habit)
        session.commit()
        session.refresh(completed_habit)
        return completed_habit
    else:
        message = f'Habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/categories/{category_id}/', response_model=schemas.HabitCategory, status_code=status.HTTP_200_OK)
async def read_one_category(category_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.HabitCategory, category_id):
        return habit
    else:
        message = f'Habit Category {category_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/categories/{category_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.HabitCategory, category_id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Habit Category {category_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/completed/{completed_id}/', response_model=schemas.HabitCompleted, status_code=status.HTTP_200_OK)
async def read_one_completed(completed_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.HabitCompleted, completed_id):
        return habit
    else:
        message = f'Habit Completed {completed_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/completed/{completed_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_completed(completed_id: int, session: Session = Depends(sqlalchemy_session)):
    if habit := session.get(models.HabitCompleted, completed_id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Habit Completed {completed_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
