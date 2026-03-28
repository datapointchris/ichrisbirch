from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.models.project import ProjectItemDependency
from ichrisbirch.models.project import ProjectItemMembership

logger = structlog.get_logger()
router = APIRouter()


def _get_item_or_404(session: Session, item_id: int) -> models.ProjectItem:
    item = session.get(models.ProjectItem, item_id)
    if not item:
        raise NotFoundException('project_item', item_id, logger)
    return item


def _detect_dependency_cycle(session: Session, item_id: int, depends_on_id: int) -> bool:
    """Check if adding item_id -> depends_on_id would create a cycle.

    Walk forward from depends_on_id through existing dependencies.
    If we reach item_id, adding this edge would create a cycle.
    """
    visited: set[int] = set()
    queue = [depends_on_id]

    while queue:
        current = queue.pop()
        if current == item_id:
            return True
        if current in visited:
            continue
        visited.add(current)

        deps = session.execute(select(ProjectItemDependency.depends_on_id).where(ProjectItemDependency.item_id == current)).scalars().all()
        queue.extend(deps)

    return False


# --- Filters (must be before /{id}/ routes) ---


@router.get('/blocked/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def list_blocked(session: Session = Depends(get_sqlalchemy_session)):
    """List items that have at least one incomplete dependency."""
    query = (
        select(models.ProjectItem)
        .where(
            models.ProjectItem.id.in_(
                select(ProjectItemDependency.item_id)
                .join(models.ProjectItem, ProjectItemDependency.depends_on_id == models.ProjectItem.id)
                .where(models.ProjectItem.completed == False)  # noqa: E712
            )
        )
        .where(models.ProjectItem.completed == False)  # noqa: E712
        .where(models.ProjectItem.archived == False)  # noqa: E712
    )
    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(get_sqlalchemy_session)):
    logger.debug('project_item_search', query=q)
    query = (
        select(models.ProjectItem)
        .where(models.ProjectItem.title.ilike(f'%{q}%') | models.ProjectItem.notes.ilike(f'%{q}%'))
        .order_by(models.ProjectItem.created_at.desc())
    )
    results = list(session.scalars(query).all())
    logger.debug('project_item_search_results', count=len(results))
    return results


# --- CRUD ---


@router.post('/', response_model=schemas.ProjectItemDetail, status_code=status.HTTP_201_CREATED)
async def create(item: schemas.ProjectItemCreate, session: Session = Depends(get_sqlalchemy_session)):
    if not item.project_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='At least one project_id is required',
        )

    # Verify all projects exist
    for pid in item.project_ids:
        if not session.get(models.Project, pid):
            raise NotFoundException('project', pid, logger)

    db_item = models.ProjectItem(title=item.title, notes=item.notes)
    session.add(db_item)
    session.flush()

    for pid in item.project_ids:
        # Auto-assign position as next in project
        max_pos = session.scalar(
            select(ProjectItemMembership.position)
            .where(ProjectItemMembership.project_id == pid)
            .order_by(ProjectItemMembership.position.desc())
            .limit(1)
        )
        next_pos = (max_pos or 0) + 1 if max_pos is not None else 0

        membership = ProjectItemMembership(item_id=db_item.id, project_id=pid, position=next_pos)
        session.add(membership)

    session.commit()
    session.refresh(db_item)

    return schemas.ProjectItemDetail(
        id=db_item.id,
        title=db_item.title,
        notes=db_item.notes,
        completed=db_item.completed,
        archived=db_item.archived,
        created_at=db_item.created_at,
        updated_at=db_item.updated_at,
        project_ids=item.project_ids,
        dependency_ids=[],
    )


@router.get('/{id}/', response_model=schemas.ProjectItemDetail, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    item = _get_item_or_404(session, id)

    project_ids = list(session.execute(select(ProjectItemMembership.project_id).where(ProjectItemMembership.item_id == id)).scalars().all())
    dependency_ids = list(
        session.execute(select(ProjectItemDependency.depends_on_id).where(ProjectItemDependency.item_id == id)).scalars().all()
    )

    return schemas.ProjectItemDetail(
        id=item.id,
        title=item.title,
        notes=item.notes,
        completed=item.completed,
        archived=item.archived,
        created_at=item.created_at,
        updated_at=item.updated_at,
        project_ids=project_ids,
        dependency_ids=dependency_ids,
    )


@router.patch('/{id}/', response_model=schemas.ProjectItem, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ProjectItemUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('project_item_update', item_id=id, update_data=update_data)

    item = _get_item_or_404(session, id)
    for attr, value in update_data.items():
        setattr(item, attr, value)
    item.updated_at = datetime.now(tz=ZoneInfo('UTC'))
    session.commit()
    session.refresh(item)
    return item


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    item = _get_item_or_404(session, id)
    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Reorder ---


@router.patch('/{id}/reorder/', response_model=schemas.ProjectItemInProject, status_code=status.HTTP_200_OK)
async def reorder(id: int, reorder: schemas.ProjectItemReorder, session: Session = Depends(get_sqlalchemy_session)):
    item = _get_item_or_404(session, id)

    membership = session.get(ProjectItemMembership, (id, reorder.project_id))
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Item {id} is not in project {reorder.project_id}',
        )

    membership.position = reorder.position
    session.commit()
    session.refresh(item)

    return schemas.ProjectItemInProject(
        id=item.id,
        title=item.title,
        notes=item.notes,
        completed=item.completed,
        archived=item.archived,
        created_at=item.created_at,
        updated_at=item.updated_at,
        position=membership.position,
    )


# --- Multi-project membership ---


@router.get('/{id}/projects/', response_model=list[schemas.Project], status_code=status.HTTP_200_OK)
async def list_projects(id: int, session: Session = Depends(get_sqlalchemy_session)):
    _get_item_or_404(session, id)

    query = (
        select(models.Project)
        .join(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
        .where(ProjectItemMembership.item_id == id)
        .order_by(models.Project.position.asc())
    )
    return list(session.scalars(query).all())


@router.post('/{id}/projects/', response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def add_to_project(id: int, membership: schemas.ProjectItemMembershipCreate, session: Session = Depends(get_sqlalchemy_session)):
    _get_item_or_404(session, id)

    if not session.get(models.Project, membership.project_id):
        raise NotFoundException('project', membership.project_id, logger)

    existing = session.get(ProjectItemMembership, (id, membership.project_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Item {id} is already in project {membership.project_id}',
        )

    max_pos = session.scalar(
        select(ProjectItemMembership.position)
        .where(ProjectItemMembership.project_id == membership.project_id)
        .order_by(ProjectItemMembership.position.desc())
        .limit(1)
    )
    next_pos = (max_pos or 0) + 1 if max_pos is not None else 0

    db_membership = ProjectItemMembership(item_id=id, project_id=membership.project_id, position=next_pos)
    session.add(db_membership)
    session.commit()

    return session.get(models.Project, membership.project_id)


@router.delete('/{id}/projects/{project_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_project(id: int, project_id: int, session: Session = Depends(get_sqlalchemy_session)):
    _get_item_or_404(session, id)

    membership = session.get(ProjectItemMembership, (id, project_id))
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Item {id} is not in project {project_id}',
        )

    # Must stay in at least one project
    total = len(session.execute(select(ProjectItemMembership.project_id).where(ProjectItemMembership.item_id == id)).all())
    if total <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Cannot remove item from its last project. Delete the item instead.',
        )

    session.delete(membership)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Dependencies ---


@router.post('/{id}/dependencies/', response_model=schemas.ProjectItemDetail, status_code=status.HTTP_201_CREATED)
async def add_dependency(id: int, dep: schemas.ProjectItemDependencyCreate, session: Session = Depends(get_sqlalchemy_session)):
    _get_item_or_404(session, id)
    _get_item_or_404(session, dep.depends_on_id)

    if id == dep.depends_on_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='An item cannot depend on itself')

    existing = session.get(ProjectItemDependency, (id, dep.depends_on_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Dependency already exists: item {id} depends on {dep.depends_on_id}',
        )

    if _detect_dependency_cycle(session, id, dep.depends_on_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Adding dependency would create a cycle: {id} -> {dep.depends_on_id}',
        )

    db_dep = ProjectItemDependency(item_id=id, depends_on_id=dep.depends_on_id)
    session.add(db_dep)
    session.commit()

    # Return full detail
    return await read_one(id, session)


@router.delete('/{id}/dependencies/{dep_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def remove_dependency(id: int, dep_id: int, session: Session = Depends(get_sqlalchemy_session)):
    dep = session.get(ProjectItemDependency, (id, dep_id))
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No dependency: item {id} -> {dep_id}',
        )

    session.delete(dep)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{id}/blockers/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def get_blockers(id: int, session: Session = Depends(get_sqlalchemy_session)):
    """Get incomplete dependencies (items that block this item)."""
    _get_item_or_404(session, id)

    query = (
        select(models.ProjectItem)
        .join(ProjectItemDependency, models.ProjectItem.id == ProjectItemDependency.depends_on_id)
        .where(ProjectItemDependency.item_id == id)
        .where(models.ProjectItem.completed == False)  # noqa: E712
    )
    return list(session.scalars(query).all())
