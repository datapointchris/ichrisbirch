import logging
from typing import Optional
from typing import Union

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger('api.habits')
router = APIRouter()


@router.post('/', response_model=schemas.Habit, status_code=status.HTTP_201_CREATED)
async def create_habit(habit: schemas.HabitCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.Habit(**habit.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/", response_model=list[schemas.Habit], status_code=status.HTTP_200_OK)
async def read_many_habits(
    session: Session = Depends(get_sqlalchemy_session), current: Optional[bool] = None, limit: Optional[int] = None
):
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


@router.get("/categories/", response_model=list[schemas.HabitCategory], status_code=status.HTTP_200_OK)
async def read_many_categories(
    session: Session = Depends(get_sqlalchemy_session), current: Optional[bool] = None, limit: Optional[int] = None
):
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


@router.get("/completed/", response_model=list[schemas.HabitCompleted], status_code=status.HTTP_200_OK)
async def read_many_completed(
    session: Session = Depends(get_sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
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
            models.HabitCompleted.complete_date >= start_date, models.HabitCompleted.complete_date <= end_date
        )
        query = query.order_by(models.HabitCompleted.complete_date.desc())

    return list(session.scalars(query).all())


@router.get('/{habit_id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def read_one_habit(habit_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.Habit, habit_id):
        return habit
    else:
        message = f'Habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.patch('/{habit_id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def update_habit(
    habit_id: int, habit_update: schemas.HabitUpdate, session: Session = Depends(get_sqlalchemy_session)
):
    if habit := session.get(models.Habit, habit_id):
        for attr, value in habit_update.model_dump().items():
            if value is not None:
                setattr(habit, attr, value)
        session.commit()
        session.refresh(habit)
        return habit
    else:
        message = f'habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{habit_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.Habit, habit_id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'habit {habit_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/categories/{category_id}/', response_model=schemas.HabitCategory, status_code=status.HTTP_200_OK)
async def read_one_category(category_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.HabitCategory, category_id):
        return habit
    else:
        message = f'habit category {category_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


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
    else:
        message = f'habit category {category_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


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
    else:
        message = f'Habit category {category_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/completed/{completed_id}/', response_model=schemas.HabitCompleted, status_code=status.HTTP_200_OK)
async def read_one_completed(completed_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.HabitCompleted, completed_id):
        return habit
    else:
        message = f'Habit Completed {completed_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/completed/{completed_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_completed(completed_id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.HabitCompleted, completed_id):
        session.delete(habit)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Habit Completed {completed_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
