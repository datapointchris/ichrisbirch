import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.models.project import ProjectItemMembership

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.ProjectWithItemCount], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(get_sqlalchemy_session)):
    query = (
        select(
            models.Project,
            func.count(ProjectItemMembership.item_id).label('item_count'),
        )
        .outerjoin(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
        .group_by(models.Project.id)
        .order_by(models.Project.position.asc())
    )
    return [
        schemas.ProjectWithItemCount(
            id=project.id,
            name=project.name,
            position=project.position,
            created_at=project.created_at,
            item_count=item_count,
        )
        for project, item_count in session.execute(query).all()
    ]


@router.post('/', response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create(project: schemas.ProjectCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.Project(**project.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.ProjectWithItemCount, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    project = session.get(models.Project, id)
    if not project:
        raise NotFoundException('project', id, logger)

    item_count = session.scalar(select(func.count(ProjectItemMembership.item_id)).where(ProjectItemMembership.project_id == id))
    return schemas.ProjectWithItemCount(
        id=project.id,
        name=project.name,
        position=project.position,
        created_at=project.created_at,
        item_count=item_count or 0,
    )


@router.patch('/{id}/', response_model=schemas.Project, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ProjectUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('project_update', project_id=id, update_data=update_data)

    if project := session.get(models.Project, id):
        for attr, value in update_data.items():
            setattr(project, attr, value)
        session.commit()
        session.refresh(project)
        return project

    raise NotFoundException('project', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    project = session.get(models.Project, id)
    if not project:
        raise NotFoundException('project', id, logger)

    # Check for items that only belong to this project (would become orphans)
    orphan_query = (
        select(ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == id)
        .where(~ProjectItemMembership.item_id.in_(select(ProjectItemMembership.item_id).where(ProjectItemMembership.project_id != id)))
    )
    orphan_count = len(session.execute(orphan_query).all())
    if orphan_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Cannot delete project: {orphan_count} item(s) belong only to this project. Move or delete them first.',
        )

    session.delete(project)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{id}/items/', response_model=list[schemas.ProjectItemInProject], status_code=status.HTTP_200_OK)
async def list_items(
    id: int,
    session: Session = Depends(get_sqlalchemy_session),
    archived: bool = Query(False, description='Include archived items'),
):
    if not session.get(models.Project, id):
        raise NotFoundException('project', id, logger)

    query = (
        select(models.ProjectItem, ProjectItemMembership.position)
        .join(ProjectItemMembership, models.ProjectItem.id == ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == id)
    )
    if not archived:
        query = query.where(models.ProjectItem.archived == False)  # noqa: E712

    query = query.order_by(ProjectItemMembership.position.asc())

    return [
        schemas.ProjectItemInProject(
            id=item.id,
            title=item.title,
            notes=item.notes,
            completed=item.completed,
            archived=item.archived,
            created_at=item.created_at,
            updated_at=item.updated_at,
            position=position,
        )
        for item, position in session.execute(query).all()
    ]
