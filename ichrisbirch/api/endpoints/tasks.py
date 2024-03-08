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
async def read_many(
    session: Session = Depends(sqlalchemy_session), completed_filter: Optional[str] = None, limit: Optional[int] = None
):
    """API method to read many tasks"""
    logger.debug(f'{completed_filter=}')

    query = select(models.Task)
    if completed_filter == 'completed':
        query = query.filter(models.Task.complete_date.is_not(None))

    if completed_filter == 'not_completed':
        query = query.filter(models.Task.complete_date.is_(None))

    query = query.order_by(models.Task.priority.asc(), models.Task.add_date.asc())
    if limit:
        query = query.limit(limit)
    return list(session.scalars(query).all())


@router.get("/completed/", response_model=list[schemas.TaskCompleted], status_code=status.HTTP_200_OK)
async def completed(
    session: Session = Depends(sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
):
    """API method to get completed tasks"""
    query = select(models.Task).filter(models.Task.complete_date.is_not(None))

    if first:  # first completed task
        query = query.order_by(models.Task.complete_date.asc()).limit(1)

    elif last:  # most recent (last) completed task
        query = query.order_by(models.Task.complete_date.desc()).limit(1)

    elif start_date is None or end_date is None:  # return all if no start or end date
        query = query.order_by(models.Task.complete_date.desc())

    else:  # filtered by start and end date
        query = query.filter(models.Task.complete_date >= start_date, models.Task.complete_date <= end_date).order_by(
            models.Task.complete_date.desc()
        )

    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(sqlalchemy_session)):
    """API method to search for tasks"""
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
    """API method to create a new task"""
    db_obj = models.Task(**task.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{task_id}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def read_one(task_id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to read one task"""
    if task := session.get(models.Task, task_id):
        return task
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{task_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(task_id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to delete a task"""
    if task := session.get(models.Task, task_id):
        session.delete(task)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Task {task_id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.post('/complete/{task_id}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def complete(task_id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to complete a task"""
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
