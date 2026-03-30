from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.models.project import ProjectItemTask
from ichrisbirch.schemas.project_item_task import ProjectItemTask as ProjectItemTaskSchema
from ichrisbirch.schemas.project_item_task import ProjectItemTaskCreate
from ichrisbirch.schemas.project_item_task import ProjectItemTaskUpdate

logger = structlog.get_logger()
router = APIRouter()


def _get_item_or_404(session: Session, item_id: UUID) -> models.ProjectItem:
    item = session.get(models.ProjectItem, item_id)
    if not item:
        raise NotFoundException('project_item', item_id, logger)
    return item


def _get_task_or_404(session: Session, item_id: UUID, task_id: UUID) -> ProjectItemTask:
    task = session.get(ProjectItemTask, task_id)
    if not task or task.item_id != item_id:
        raise NotFoundException('project_item_task', task_id, logger)
    return task


@router.get('/', response_model=list[ProjectItemTaskSchema], status_code=status.HTTP_200_OK)
async def list_tasks(item_id: UUID, session: Session = Depends(get_sqlalchemy_session)):
    """List all tasks for a project item, ordered by position."""
    _get_item_or_404(session, item_id)
    query = select(ProjectItemTask).where(ProjectItemTask.item_id == item_id).order_by(ProjectItemTask.position.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=ProjectItemTaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(item_id: UUID, task: ProjectItemTaskCreate, session: Session = Depends(get_sqlalchemy_session)):
    """Create a new task on a project item."""
    _get_item_or_404(session, item_id)

    # Auto-assign position if default (0) and tasks already exist
    position = task.position
    if position == 0:
        max_pos = session.scalar(
            select(ProjectItemTask.position).where(ProjectItemTask.item_id == item_id).order_by(ProjectItemTask.position.desc()).limit(1)
        )
        if max_pos is not None:
            position = max_pos + 1

    db_task = ProjectItemTask(item_id=item_id, title=task.title, position=position)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.patch('/{task_id}/', response_model=ProjectItemTaskSchema, status_code=status.HTTP_200_OK)
async def update_task(item_id: UUID, task_id: UUID, update: ProjectItemTaskUpdate, session: Session = Depends(get_sqlalchemy_session)):
    """Update a project item task."""
    task = _get_task_or_404(session, item_id, task_id)
    for attr, value in update.model_dump(exclude_unset=True).items():
        setattr(task, attr, value)
    session.commit()
    session.refresh(task)
    return task


@router.delete('/{task_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(item_id: UUID, task_id: UUID, session: Session = Depends(get_sqlalchemy_session)):
    """Delete a project item task."""
    task = _get_task_or_404(session, item_id, task_id)
    session.delete(task)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
