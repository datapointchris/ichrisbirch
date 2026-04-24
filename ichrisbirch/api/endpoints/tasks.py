from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.services.task_priorities import compact_incomplete_task_priorities

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession, limit: int | None = None):
    query = select(models.Task).order_by(models.Task.priority.asc(), models.Task.add_date.asc()).limit(limit)
    return list(session.scalars(query).all())


@router.get('/todo/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def todo(
    session: DbSession,
    limit: int | None = None,
    priority: tuple[int, int] | None = None,
):
    """Priority is a tuple of INCLUSIVE priority values."""
    query = select(models.Task).filter(models.Task.complete_date.is_(None))
    if priority:
        query = query.filter(models.Task.priority >= priority[0], models.Task.priority <= priority[1])

    query = query.order_by(models.Task.priority.asc(), models.Task.add_date.asc()).limit(limit)
    return list(session.scalars(query).all())


@router.get('/completed/', response_model=list[schemas.TaskCompleted], status_code=status.HTTP_200_OK)
async def completed(
    session: DbSession,
    start_date: str | None = None,
    end_date: str | None = None,
    first: bool | None = None,
    last: bool | None = None,
):
    query = select(models.Task).filter(models.Task.complete_date.is_not(None))

    if first:  # first completed task
        query = query.order_by(models.Task.complete_date.asc()).limit(1)

    elif last:  # most recent (last) completed task
        query = query.order_by(models.Task.complete_date.desc()).limit(1)

    elif start_date is None or end_date is None:  # return all if no start or end date
        query = query.order_by(models.Task.complete_date.desc())

    else:  # filtered by start and end date
        # Explicit parsing - dates come as strings from query params
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Invalid date format: {e}. Expected ISO format (e.g., 2020-04-01T00:00:00)',
            ) from e
        query = query.filter(models.Task.complete_date >= start_dt, models.Task.complete_date <= end_dt)
        query = query.order_by(models.Task.complete_date.desc())

    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def search(q: str, session: DbSession):
    logger.debug('task_search', query=q)
    tasks = (
        select(models.Task)
        .filter(models.Task.name.ilike('%' + q + '%') | models.Task.notes.ilike('%' + q + '%'))
        .order_by(models.Task.complete_date.desc(), models.Task.add_date.asc())
    )
    results = session.scalars(tasks).all()
    logger.debug('task_search_results', count=len(results))
    return results


@router.post('/', response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create(task: schemas.TaskCreate, session: DbSession):
    db_obj = models.Task(**task.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.post('/reorder/', status_code=status.HTTP_200_OK)
async def reorder(session: DbSession):
    """Dense-rank incomplete tasks to priorities 1..K, tiebreak by add_date.

    Same operation the nightly scheduler runs, exposed for on-demand use
    when the user wants priorities tidied up immediately.
    """
    count = compact_incomplete_task_priorities(session)
    session.commit()
    logger.info('task_priorities_reordered', count=count)
    if count == 0:
        return {'message': 'No tasks to reorder'}
    return {'message': f'Reordered {count} tasks'}


@router.get('/{id}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if task := session.get(models.Task, id):
        return task
    raise NotFoundException('task', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if task := session.get(models.Task, id):
        session.delete(task)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('task', id, logger)


@router.patch('/{id}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.TaskUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('task_update', task_id=id, update_data=update_data)

    if task := session.get(models.Task, id):
        for attr, value in update_data.items():
            setattr(task, attr, value)
        session.commit()
        session.refresh(task)
        return task

    raise NotFoundException('task', id, logger)


@router.patch('/{task_id}/complete/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def complete(task_id: int, session: DbSession):
    if task := session.get(models.Task, task_id):
        task.complete_date = datetime.now(tz=ZoneInfo('America/Chicago')).isoformat()  # type: ignore
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    raise NotFoundException('task', task_id, logger)


@router.patch('/{task_id}/shift/{positions}/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def shift(task_id: int, positions: int, session: DbSession):
    """Shift the task's priority rank by `positions` (positive = down, negative = up).

    Priority is a positional rank — lower numbers are higher priority.
    Positive values push the task down the list; negative values push it
    up. Nightly compaction absorbs any gaps the shift creates.
    """
    if task := session.get(models.Task, task_id):
        task.priority += positions
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    raise NotFoundException('task', task_id, logger)
