from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.models.project import ProjectItemTask
from ichrisbirch.schemas.project_item_task import ProjectItemTask as ProjectItemTaskSchema
from ichrisbirch.schemas.project_item_task import ProjectItemTaskCreate
from ichrisbirch.schemas.project_item_task import ProjectItemTaskUpdate
from ichrisbirch.services.project_refs import resolve_item

logger = structlog.get_logger()
router = APIRouter()


def path_item(item_id: str, session: DbSession) -> models.ProjectItem:
    """Resolve the `{item_id}` segment, which is a UUID or an item number."""
    return resolve_item(session, item_id)


ItemFromPath = Annotated[models.ProjectItem, Depends(path_item)]


def _get_task_or_404(session: Session, item_id: UUID, task_id: UUID) -> ProjectItemTask:
    task = session.get(ProjectItemTask, task_id)
    if not task or task.item_id != item_id:
        raise NotFoundException('project_item_task', task_id, logger)
    return task


@router.get('/', response_model=list[ProjectItemTaskSchema], status_code=status.HTTP_200_OK)
async def list_tasks(item: ItemFromPath, session: DbSession):
    """List all tasks for a project item, ordered by position."""
    query = select(ProjectItemTask).where(ProjectItemTask.item_id == item.id).order_by(ProjectItemTask.position.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=ProjectItemTaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(item: ItemFromPath, task: ProjectItemTaskCreate, session: DbSession):
    """Create a new task on a project item."""
    # Auto-assign position if default (0) and tasks already exist
    position = task.position
    if position == 0:
        max_pos = session.scalar(
            select(ProjectItemTask.position).where(ProjectItemTask.item_id == item.id).order_by(ProjectItemTask.position.desc()).limit(1)
        )
        if max_pos is not None:
            position = max_pos + 1

    db_task = ProjectItemTask(item_id=item.id, title=task.title, position=position)
    if task.id is not None:
        db_task.id = task.id
    session.add(db_task)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Task with id {task.id} already exists') from None
    session.refresh(db_task)
    return db_task


@router.patch('/{task_id}/', response_model=ProjectItemTaskSchema, status_code=status.HTTP_200_OK)
async def update_task(item: ItemFromPath, task_id: UUID, update: ProjectItemTaskUpdate, session: DbSession):
    """Update a project item task."""
    task = _get_task_or_404(session, item.id, task_id)
    for attr, value in update.model_dump(exclude_unset=True).items():
        setattr(task, attr, value)
    session.commit()
    session.refresh(task)
    return task


@router.delete('/{task_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(item: ItemFromPath, task_id: UUID, session: DbSession):
    """Delete a project item task."""
    task = _get_task_or_404(session, item.id, task_id)
    session.delete(task)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
