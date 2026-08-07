from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.models.project import ProjectItemMembership

logger = structlog.get_logger()
router = APIRouter()


def item_count_columns():
    """Total, open, and completed counts, aggregated in one pass over the join.

    Conditional aggregation rather than three queries: a caller listing every
    project needs the breakdown for all of them, and the counts are what make
    the list answer "which of these still has work in it".
    """
    not_archived = models.ProjectItem.archived.is_(False)
    return (
        func.count(ProjectItemMembership.item_id).label('item_count'),
        func.count(ProjectItemMembership.item_id).filter(not_archived, models.ProjectItem.completed.is_(False)).label('open_count'),
        func.count(ProjectItemMembership.item_id).filter(not_archived, models.ProjectItem.completed.is_(True)).label('completed_count'),
    )


@router.get('/', response_model=list[schemas.ProjectWithItemCount], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession):
    query = (
        select(models.Project, *item_count_columns())
        .outerjoin(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
        .outerjoin(models.ProjectItem, ProjectItemMembership.item_id == models.ProjectItem.id)
        .group_by(models.Project.id)
        .order_by(models.Project.position.asc())
    )
    return [
        schemas.ProjectWithItemCount(
            id=project.id,
            name=project.name,
            description=project.description,
            kind=project.kind,
            position=project.position,
            created_at=project.created_at,
            item_count=item_count,
            open_count=open_count,
            completed_count=completed_count,
        )
        for project, item_count, open_count, completed_count in session.execute(query).all()
    ]


def validate_kind(kind: str, session: Session) -> None:
    """Reject an unknown kind here rather than letting the FK raise.

    Checked against the lookup table instead of a `Literal` so adding a kind
    stays an insert — which is the whole reason the categorical is a table and
    not an enum type.
    """
    if session.get(models.ProjectKind, kind) is None:
        known = session.scalars(select(models.ProjectKind.name).order_by(models.ProjectKind.name)).all()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown project kind {kind!r}. Known kinds: {", ".join(known)}',
        )


@router.post('/', response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create(project: schemas.ProjectCreate, session: DbSession):
    validate_kind(project.kind, session)
    db_obj = models.Project(**project.model_dump(exclude={'id'}))
    if project.id is not None:
        db_obj.id = project.id
    session.add(db_obj)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Project with id {project.id} already exists') from None
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.ProjectWithItemCount, status_code=status.HTTP_200_OK)
async def read_one(id: UUID, session: DbSession):
    project = session.get(models.Project, id)
    if not project:
        raise NotFoundException('project', id, logger)

    counts = (
        select(*item_count_columns())
        .select_from(ProjectItemMembership)
        .outerjoin(models.ProjectItem, ProjectItemMembership.item_id == models.ProjectItem.id)
        .where(ProjectItemMembership.project_id == id)
    )
    item_count, open_count, completed_count = session.execute(counts).one()
    return schemas.ProjectWithItemCount(
        id=project.id,
        name=project.name,
        description=project.description,
        kind=project.kind,
        position=project.position,
        created_at=project.created_at,
        item_count=item_count,
        open_count=open_count,
        completed_count=completed_count,
    )


@router.patch('/{id}/', response_model=schemas.Project, status_code=status.HTTP_200_OK)
async def update(id: UUID, update: schemas.ProjectUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('project_update', project_id=id, update_data=update_data)
    if (kind := update_data.get('kind')) is not None:
        validate_kind(kind, session)

    if project := session.get(models.Project, id):
        for attr, value in update_data.items():
            setattr(project, attr, value)
        session.commit()
        session.refresh(project)
        return project

    raise NotFoundException('project', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: UUID, session: DbSession):
    project = session.get(models.Project, id)
    if not project:
        raise NotFoundException('project', id, logger)

    # Find items that only belong to this project (would become orphans)
    multi_project_items = select(ProjectItemMembership.item_id).where(ProjectItemMembership.project_id != id)
    orphan_query = (
        select(models.ProjectItem)
        .join(ProjectItemMembership, models.ProjectItem.id == ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == id)
        .where(~models.ProjectItem.id.in_(multi_project_items))
    )
    orphan_items = session.execute(orphan_query).scalars().all()

    # Auto-delete completed orphans; block only on incomplete ones
    incomplete_orphans = [item for item in orphan_items if not item.completed]
    if incomplete_orphans:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f'Cannot delete project: {len(incomplete_orphans)} incomplete item(s) belong only to this project.'
                ' Complete, move, or delete them first.'
            ),
        )

    for item in orphan_items:
        session.delete(item)

    session.delete(project)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{id}/items/', response_model=list[schemas.ProjectItemInProject], status_code=status.HTTP_200_OK)
async def list_items(
    id: UUID,
    session: DbSession,
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

    # position has no unique constraint, so a collision would otherwise order by
    # whatever the database returned
    query = query.order_by(ProjectItemMembership.position.asc(), models.ProjectItem.created_at.asc())

    return [
        schemas.ProjectItemInProject(
            id=item.id,
            title=item.title,
            notes=item.notes,
            repo=item.repo,
            completed=item.completed,
            archived=item.archived,
            created_at=item.created_at,
            updated_at=item.updated_at,
            position=position,
        )
        for item, position in session.execute(query).all()
    ]
