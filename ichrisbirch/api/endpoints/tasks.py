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


@router.get("/", response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(sqlalchemy_session), limit: Optional[int] = None):
    query = select(models.Task).order_by(models.Task.priority.asc(), models.Task.add_date.asc()).limit(limit)
    return list(session.scalars(query).all())


@router.get("/todo/", response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def todo(
    session: Session = Depends(sqlalchemy_session),
    limit: Optional[int] = None,
    priority: Optional[tuple[int, int]] = None,
):
    """Priority is a tuple of INCLUSIVE priority values."""
    logger.debug(f'{priority=}')
    query = select(models.Task).filter(models.Task.complete_date.is_(None))
    if priority:
        query = query.filter(models.Task.priority >= priority[0], models.Task.priority <= priority[1])

    query = query.order_by(models.Task.priority.asc(), models.Task.add_date.asc()).limit(limit)
    return list(session.scalars(query).all())


@router.get("/completed/", response_model=list[schemas.TaskCompleted], status_code=status.HTTP_200_OK)
async def completed(
    session: Session = Depends(sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
):
    logger.debug(f'Parameters passed: {start_date=}, {end_date=}, {first=}, {last=}')
    query = select(models.Task).filter(models.Task.complete_date.is_not(None))

    if first:  # first completed task
        query = query.order_by(models.Task.complete_date.asc()).limit(1)

    elif last:  # most recent (last) completed task
        query = query.order_by(models.Task.complete_date.desc()).limit(1)

    elif start_date is None or end_date is None:  # return all if no start or end date
        query = query.order_by(models.Task.complete_date.desc())

    else:  # filtered by start and end date
        query = query.filter(models.Task.complete_date >= start_date, models.Task.complete_date <= end_date)
        query = query.order_by(models.Task.complete_date.desc())

    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(sqlalchemy_session)):
    logger.debug(f'searching for {q=}')
    tasks = (
        select(models.Task)
        .filter(models.Task.name.ilike('%' + q + '%') | models.Task.notes.ilike('%' + q + '%'))
        .order_by(models.Task.complete_date.desc(), models.Task.add_date.asc())
    )
    results = session.scalars(tasks).all()
    logger.debug(f'search found {len(results)} results')
    return results


@router.post('/', response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create(task: schemas.TaskCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.Task(**task.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{task_id}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def read_one(task_id: int, session: Session = Depends(sqlalchemy_session)):
    if task := session.get(models.Task, task_id):
        return task
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{task_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(task_id: int, session: Session = Depends(sqlalchemy_session)):
    if task := session.get(models.Task, task_id):
        session.delete(task)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.patch('/{task_id}/complete/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def complete(task_id: int, session: Session = Depends(sqlalchemy_session)):
    if task := session.get(models.Task, task_id):
        task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()  # type: ignore
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.patch('/{task_id}/extend/{days}', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def extend(task_id: int, days: int, session: Session = Depends(sqlalchemy_session)):
    if task := session.get(models.Task, task_id):
        task.priority += days
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
