from datetime import datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.models.project import ITEM_STATUSES
from ichrisbirch.models.project import ProjectItemDependency
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.services.project_item_positions import move_membership_to_position
from ichrisbirch.services.project_refs import resolve_item
from ichrisbirch.services.project_refs import resolve_project

logger = structlog.get_logger()
router = APIRouter()

# schemas.ProjectItem embeds memberships, dependency ids, and tasks, so every
# endpoint returning it must load all three up front or serialization lazy-loads
# three times per item — the N+1 this embedding exists to remove, moved from HTTP
# into SQL. Applied as one name so a new list endpoint cannot pick a subset.
PROJECT_ITEM_LOAD_OPTIONS = (
    selectinload(models.ProjectItem.projects),
    selectinload(models.ProjectItem.dependencies),
    selectinload(models.ProjectItem.tasks),
)


# The repo tag is the axis that crosses projects: it outlives the project an item
# was filed under, so it is the only way to ask what work a repo has accumulated
# across finished and live efforts alike. Every collection read takes it.
RepoFilter = Annotated[str | None, Query(description='Only items tagged with this repo registry name')]


def apply_repo_filter(query: Select, repo: str | None) -> Select:
    """Narrow a project-item query to one repo, or leave it alone when unset.

    An explicit `repo=` (empty string) means the untagged items — the ones that
    are not repo work at all — which is a different question from "any repo" and
    has to stay askable.
    """
    if repo is None:
        return query
    if repo == '':
        return query.where(models.ProjectItem.repo.is_(None))
    return query.where(models.ProjectItem.repo == repo)


def path_item(id: str, session: DbSession) -> models.ProjectItem:
    """Resolve the `{id}` segment, which is a UUID or an item number."""
    return resolve_item(session, id)


def path_dependency_item(dep_id: str, session: DbSession) -> models.ProjectItem:
    return resolve_item(session, dep_id)


def path_project(project_id: str, session: DbSession) -> models.Project:
    """Resolve the `{project_id}` segment, which is a UUID or a project name."""
    return resolve_project(session, project_id)


# Endpoints take the resolved row rather than the raw segment: every one of them
# had to fetch it anyway, and taking the id would mean each deciding for itself
# whether the caller had handed over a key or a handle.
ItemFromPath = Annotated[models.ProjectItem, Depends(path_item)]
DependencyItemFromPath = Annotated[models.ProjectItem, Depends(path_dependency_item)]
ProjectFromPath = Annotated[models.Project, Depends(path_project)]


def _detect_dependency_cycle(session: Session, item_id: UUID, depends_on_id: UUID) -> bool:
    """Check if adding item_id -> depends_on_id would create a cycle.

    Walk forward from depends_on_id through existing dependencies.
    If we reach item_id, adding this edge would create a cycle.
    """
    visited: set[UUID] = set()
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


def _detail(session: Session, item: models.ProjectItem) -> schemas.ProjectItemDetail:
    projects = list(
        session.scalars(
            select(models.Project)
            .join(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
            .where(ProjectItemMembership.item_id == item.id)
        ).all()
    )
    dependency_ids = list(
        session.execute(select(ProjectItemDependency.depends_on_id).where(ProjectItemDependency.item_id == item.id)).scalars().all()
    )

    return schemas.ProjectItemDetail(
        id=item.id,
        number=item.number,
        title=item.title,
        notes=item.notes,
        repo=item.repo,
        completed=item.completed,
        archived=item.archived,
        created_at=item.created_at,
        updated_at=item.updated_at,
        projects=[schemas.Project.model_validate(p) for p in projects],
        dependency_ids=dependency_ids,
    )


def _next_position_in_project(session: Session, project_id: UUID) -> int:
    max_pos = session.scalar(
        select(ProjectItemMembership.position)
        .where(ProjectItemMembership.project_id == project_id)
        .order_by(ProjectItemMembership.position.desc())
        .limit(1)
    )
    return (max_pos or 0) + 1 if max_pos is not None else 0


# --- List and filters (must be before /{id}/ routes) ---


# Not a status, so it is not in ITEM_STATUSES: `all` is the absence of the
# filter, and including it would make it look assignable to an item.
ALL_STATUSES = 'all'


def apply_status_filter(query: Select, item_status: str) -> Select:
    """Narrow to one derived status, or leave the query alone for `all`.

    `archived` beats `completed`, matching the precedence the item counts and
    every client render — so `completed` means finished and still in view, and an
    item that was completed and then archived answers to `archived` alone. Two
    booleans, three states, and no combination is reachable twice.
    """
    if item_status == ALL_STATUSES:
        return query
    if item_status == 'archived':
        return query.where(models.ProjectItem.archived == True)  # noqa: E712
    query = query.where(models.ProjectItem.archived == False)  # noqa: E712
    return query.where(models.ProjectItem.completed == (item_status == 'completed'))


def validate_item_status(item_status: str) -> None:
    """Reject an unknown status by name rather than answering with an empty list.

    No lookup table to check against, unlike a project's: an item's status is
    derived from booleans, so the vocabulary is a constant.
    """
    if item_status not in (*ITEM_STATUSES, ALL_STATUSES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown item status {item_status!r}. Known statuses: {", ".join(ITEM_STATUSES)}, all',
        )


@router.get('/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    repo: RepoFilter = None,
    item_status: str = Query(
        'open',
        alias='status',
        description="An item status, or 'all'. Completed and archived items are hidden by default.",
    ),
):
    """List open project items — not completed, not archived.

    The default narrows because completed items accumulate without bound, which
    is the test `cli-design.md` § "A default narrows only where the hidden class
    grows without bound" applies. Measured 2026-08-12, before this existed: 213
    completed against 213 open, so the default read of the store was half
    history and nothing was going to stop that growing.
    """
    validate_item_status(item_status)
    query = select(models.ProjectItem).options(*PROJECT_ITEM_LOAD_OPTIONS).order_by(models.ProjectItem.created_at.desc())
    query = apply_status_filter(query, item_status)
    query = apply_repo_filter(query, repo)
    return list(session.scalars(query).all())


@router.get('/blocked/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def list_blocked(session: DbSession, repo: RepoFilter = None):
    """List items that have at least one incomplete dependency."""
    query = (
        select(models.ProjectItem)
        .options(*PROJECT_ITEM_LOAD_OPTIONS)
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
    query = apply_repo_filter(query, repo)
    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def search(q: str, session: DbSession, repo: RepoFilter = None):
    logger.debug('project_item_search', query=q)
    query = (
        select(models.ProjectItem)
        .options(*PROJECT_ITEM_LOAD_OPTIONS)
        .where(models.ProjectItem.title.ilike(f'%{q}%') | models.ProjectItem.notes.ilike(f'%{q}%'))
        .order_by(models.ProjectItem.created_at.desc())
    )
    query = apply_repo_filter(query, repo)
    results = list(session.scalars(query).all())
    logger.debug('project_item_search_results', count=len(results))
    return results


# --- CRUD ---


@router.post('/', response_model=schemas.ProjectItemDetail, status_code=status.HTTP_201_CREATED)
async def create(item: schemas.ProjectItemCreate, session: DbSession):
    if not item.project_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='At least one project_id is required',
        )

    # Resolves names as well as UUIDs, and 404s here rather than letting the
    # foreign key raise after the item row is already in the transaction.
    projects = [resolve_project(session, ref) for ref in item.project_ids]

    db_item = models.ProjectItem(title=item.title, notes=item.notes, repo=item.repo)
    if item.id is not None:
        db_item.id = item.id
    session.add(db_item)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Project item with id {item.id} already exists') from None

    for project in projects:
        membership = ProjectItemMembership(
            item_id=db_item.id, project_id=project.id, position=_next_position_in_project(session, project.id)
        )
        session.add(membership)

    session.commit()
    # The number comes from the database, not from the client, so the row has to
    # be read back before the response can carry it. It is the handle the caller
    # will use for every subsequent command, and todoui writes it into the local
    # row it just created, so leaving it to the next pull is not good enough.
    session.refresh(db_item)

    return _detail(session, db_item)


@router.get('/{id}/', response_model=schemas.ProjectItemDetail, status_code=status.HTTP_200_OK)
async def read_one(item: ItemFromPath, session: DbSession):
    return _detail(session, item)


@router.patch('/{id}/', response_model=schemas.ProjectItem, status_code=status.HTTP_200_OK)
async def update(item: ItemFromPath, update: schemas.ProjectItemUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('project_item_update', item_id=item.id, update_data=update_data)

    # Guard: cannot complete an item that has incomplete tasks
    if update_data.get('completed') is True and not item.completed:
        incomplete_tasks = [t for t in item.tasks if not t.completed]
        if incomplete_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Cannot complete item with {len(incomplete_tasks)} incomplete task(s). Finish all tasks first.',
            )

    for attr, value in update_data.items():
        setattr(item, attr, value)
    item.updated_at = datetime.now(tz=ZoneInfo('UTC'))
    session.commit()
    session.refresh(item)
    return item


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(item: ItemFromPath, session: DbSession):
    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Reorder ---


@router.patch('/{id}/reorder/', response_model=schemas.ProjectItemInProject, status_code=status.HTTP_200_OK)
async def reorder(item: ItemFromPath, reorder: schemas.ProjectItemReorder, session: DbSession):
    project = resolve_project(session, reorder.project_id)

    membership = session.get(ProjectItemMembership, (item.id, project.id))
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Item {item.number} is not in project {project.name}',
        )

    move_membership_to_position(session, project.id, item.id, reorder.position)
    session.commit()
    session.refresh(item)
    session.refresh(membership)

    return schemas.ProjectItemInProject(
        id=item.id,
        number=item.number,
        title=item.title,
        notes=item.notes,
        repo=item.repo,
        completed=item.completed,
        archived=item.archived,
        created_at=item.created_at,
        updated_at=item.updated_at,
        position=membership.position,
    )


# --- Multi-project membership ---


@router.get('/{id}/projects/', response_model=list[schemas.Project], status_code=status.HTTP_200_OK)
async def list_projects(item: ItemFromPath, session: DbSession):
    query = (
        select(models.Project)
        .join(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
        .where(ProjectItemMembership.item_id == item.id)
        .order_by(models.Project.position.asc())
    )
    return list(session.scalars(query).all())


@router.post('/{id}/projects/', response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def add_to_project(item: ItemFromPath, membership: schemas.ProjectItemMembershipCreate, session: DbSession):
    project = resolve_project(session, membership.project_id)

    if session.get(ProjectItemMembership, (item.id, project.id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Item {item.number} is already in project {project.name}',
        )

    db_membership = ProjectItemMembership(item_id=item.id, project_id=project.id, position=_next_position_in_project(session, project.id))
    session.add(db_membership)
    session.commit()

    return project


@router.delete('/{id}/projects/{project_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_project(item: ItemFromPath, project: ProjectFromPath, session: DbSession):
    membership = session.get(ProjectItemMembership, (item.id, project.id))
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Item {item.number} is not in project {project.name}',
        )

    # Must stay in at least one project
    total = len(session.execute(select(ProjectItemMembership.project_id).where(ProjectItemMembership.item_id == item.id)).all())
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
async def add_dependency(item: ItemFromPath, dep: schemas.ProjectItemDependencyCreate, session: DbSession):
    depends_on = resolve_item(session, dep.depends_on_id)

    if item.id == depends_on.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='An item cannot depend on itself')

    if session.get(ProjectItemDependency, (item.id, depends_on.id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Dependency already exists: item {item.number} depends on {depends_on.number}',
        )

    if _detect_dependency_cycle(session, item.id, depends_on.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Adding dependency would create a cycle: {item.number} -> {depends_on.number}',
        )

    session.add(ProjectItemDependency(item_id=item.id, depends_on_id=depends_on.id))
    session.commit()

    return _detail(session, item)


@router.delete('/{id}/dependencies/{dep_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def remove_dependency(item: ItemFromPath, depends_on: DependencyItemFromPath, session: DbSession):
    dep = session.get(ProjectItemDependency, (item.id, depends_on.id))
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No dependency: item {item.number} -> {depends_on.number}',
        )

    session.delete(dep)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{id}/blockers/', response_model=list[schemas.ProjectItem], status_code=status.HTTP_200_OK)
async def get_blockers(item: ItemFromPath, session: DbSession):
    """Get incomplete dependencies (items that block this item)."""
    query = (
        select(models.ProjectItem)
        .options(*PROJECT_ITEM_LOAD_OPTIONS)
        .join(ProjectItemDependency, models.ProjectItem.id == ProjectItemDependency.depends_on_id)
        .where(ProjectItemDependency.item_id == item.id)
        .where(models.ProjectItem.completed == False)  # noqa: E712
    )
    return list(session.scalars(query).all())
