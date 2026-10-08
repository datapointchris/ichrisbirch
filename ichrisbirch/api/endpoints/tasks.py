from datetime import UTC
from datetime import datetime

import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.api.request_zone import RequestZone
from ichrisbirch.models.task import TASK_CATEGORIES
from ichrisbirch.services.date_bounds import apply_date_bounds
from ichrisbirch.services.row_limit import RowLimit
from ichrisbirch.services.row_limit import apply_row_limit
from ichrisbirch.services.task_queue import in_queue_order
from ichrisbirch.services.task_queue import is_closed
from ichrisbirch.services.task_queue import is_open
from ichrisbirch.services.task_queue import match_fields_to_state
from ichrisbirch.services.task_queue import new_task
from ichrisbirch.services.task_queue import restart_window

logger = structlog.get_logger()
router = APIRouter()


# A task is open, completed or dropped — `complete_date` and `drop_date` carry
# the whole state. `all` is the absence of the filter rather than a fourth state.
TASK_STATUSES = ['open', 'completed', 'dropped']
ALL_STATUSES = 'all'


@router.get('/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    zone: RequestZone,
    limit: RowLimit = None,
    task_status: str = Query(
        'open',
        alias='status',
        description="A task status, or 'all'. Completed tasks are hidden by default.",
    ),
    category: str | None = Query(
        None,
        description='One task category. Omitted, every category is listed.',
    ),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """List tasks of one status, open by default. Open tasks come pinned first, then by `rank_at`.

    The default narrows because closed tasks accumulate without bound, per
    `cli-design.md` § "A default narrows only where the hidden class grows
    without bound". Completed and dropped tasks are ordered by when they closed,
    most recent first — their place in the queue stopped meaning anything the
    moment they left it, which is the same reason a closed project orders by
    `closed_at`.

    `/todo/` and `/completed/` answer narrower versions of this and remain for
    the web app. This is the one the CLI asks, so it has to be able to express
    every status rather than one per path.

    The date bounds narrow on `drop_date` for dropped tasks and on
    `complete_date` otherwise, so an open task is outside every range. They
    live here rather than only on `/completed/` for the same reason `status`
    does: this is the read the CLI makes, and it has to be able to express the
    whole question rather than sending the caller to another path that answers
    a different response model and ignores `limit`.

    `category` narrows here rather than in the caller, per `cli-design.md`
    § "Filtering is server-side" — a client filtering after the fact has to pull
    every row to find a handful, and `limit` would then cap the wrong set.
    """
    if task_status not in (*TASK_STATUSES, ALL_STATUSES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown task status {task_status!r}. Known statuses: {", ".join(TASK_STATUSES)}, all',
        )
    if category is not None and category not in TASK_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown task category {category!r}. Known categories: {", ".join(TASK_CATEGORIES)}',
        )

    query = select(models.Task)
    if category is not None:
        query = query.filter(models.Task.category == category)
    bound_column = models.Task.complete_date
    match task_status:
        case 'open':
            query = in_queue_order(is_open(query))
        case 'completed':
            query = query.filter(models.Task.complete_date.is_not(None)).order_by(models.Task.complete_date.desc())
        case 'dropped':
            bound_column = models.Task.drop_date
            query = query.filter(models.Task.drop_date.is_not(None)).order_by(models.Task.drop_date.desc())
        case 'all':
            query = in_queue_order(query)

    query = apply_date_bounds(query, bound_column, start_date, end_date, timezone=zone)
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.get('/todo/', response_model=list[schemas.Task], status_code=status.HTTP_200_OK)
async def todo(session: DbSession, limit: RowLimit = None):
    query = in_queue_order(is_open(select(models.Task)))
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.get('/categories/', response_model=list[schemas.TaskCategory], status_code=status.HTTP_200_OK)
async def read_categories(session: DbSession):
    """Every task category with the window a new task in it gets."""
    return list(session.scalars(select(models.TaskCategory).order_by(models.TaskCategory.name)).all())


@router.patch('/categories/{name}/', response_model=schemas.TaskCategory, status_code=status.HTTP_200_OK)
async def update_category(name: str, update: schemas.TaskCategoryUpdate, session: DbSession):
    """Change a category's window. Tasks already open keep the window they were made with."""
    if category := session.get(models.TaskCategory, name):
        for attr, value in update.model_dump(exclude_unset=True).items():
            setattr(category, attr, value)
        session.commit()
        session.refresh(category)
        logger.info('task_category_updated', name=name, window_days=category.window_days)
        return category
    raise NotFoundException('task category', name, logger)


@router.get('/completed/', response_model=list[schemas.TaskCompleted], status_code=status.HTTP_200_OK)
async def completed(
    session: DbSession,
    zone: RequestZone,
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

    else:
        query = apply_date_bounds(query, models.Task.complete_date, start_date, end_date, timezone=zone)
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
    try:
        db_obj = new_task(session, **task.model_dump())
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from e
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


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
        if task.complete_date is not None and task.drop_date is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Task {id} cannot be both completed and dropped. Clear one date to set the other.',
            )
        if update_data.get('pinned') and is_closed(task):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Task {id} is closed, so it cannot be pinned. Reopen it first.',
            )
        if update_data.get('drop_reason') is not None and task.drop_date is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Task {id} is not dropped, so it cannot have a drop reason.',
            )
        match_fields_to_state(task)
        session.commit()
        session.refresh(task)
        return task

    raise NotFoundException('task', id, logger)


def open_task(session: DbSession, task_id: int, verb: str) -> models.Task:
    """The task, or a 404 when it does not exist and a 409 when it is already closed."""
    task = session.get(models.Task, task_id)
    if task is None:
        raise NotFoundException('task', task_id, logger)
    if is_closed(task):
        state = 'completed' if task.complete_date is not None else 'dropped'
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Task {task_id} is already {state}, so it cannot be {verb}.',
        )
    return task


@router.patch('/{task_id}/complete/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def complete(task_id: int, session: DbSession):
    task = open_task(session, task_id, 'completed')
    task.complete_date = datetime.now(UTC)
    match_fields_to_state(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch('/{task_id}/drop/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def drop(task_id: int, session: DbSession, body: schemas.TaskDrop | None = None):
    """Close a task you are letting go of. It stays on record and does not count as completed."""
    task = open_task(session, task_id, 'dropped')
    task.drop_date = datetime.now(UTC)
    task.drop_reason = body.reason if body else None
    match_fields_to_state(task)
    session.commit()
    session.refresh(task)
    logger.info('task_dropped', task_id=task_id)
    return task


@router.patch('/{task_id}/reopen/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def reopen(task_id: int, session: DbSession):
    """Put a completed or dropped task back on the list at the `rank_at` it had."""
    task = session.get(models.Task, task_id)
    if task is None:
        raise NotFoundException('task', task_id, logger)
    if not is_closed(task):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Task {task_id} is already open, so it cannot be reopened.',
        )
    task.complete_date = None
    task.drop_date = None
    match_fields_to_state(task)
    session.commit()
    session.refresh(task)
    logger.info('task_reopened', task_id=task_id)
    return task


@router.patch('/{task_id}/snooze/', response_model=schemas.Task, status_code=status.HTTP_200_OK)
async def snooze(task_id: int, session: DbSession):
    """Restart the task's window from now, which moves it back down the list, and unpin it."""
    task = open_task(session, task_id, 'snoozed')
    restart_window(task)
    session.commit()
    session.refresh(task)
    logger.info('task_snoozed', task_id=task_id, rank_at=task.rank_at.isoformat())
    return task
