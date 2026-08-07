from datetime import UTC
from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.models.project import TERMINAL_PROJECT_STATUSES
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.services.project_refs import resolve_project

logger = structlog.get_logger()
router = APIRouter()

# Not a status, so it cannot live in the lookup table: `all` is the absence of
# the filter, and storing it would make it assignable to a project.
ALL_STATUSES = 'all'


def path_project(id: str, session: DbSession) -> models.Project:
    """Resolve the `{id}` segment, which is a UUID or the project's unique name.

    Projects get no short number the way items do — `name` is already unique and
    is what anyone types.
    """
    return resolve_project(session, id)


ProjectFromPath = Annotated[models.Project, Depends(path_project)]


def item_count_columns():
    """Total, open, and completed counts plus the repos, in one pass over the join.

    Conditional aggregation rather than four queries: a caller listing every
    project needs the breakdown for all of them, and the counts are what make
    the list answer "which of these still has work in it".
    """
    not_archived = models.ProjectItem.archived.is_(False)
    return (
        func.count(ProjectItemMembership.item_id).label('item_count'),
        func.count(ProjectItemMembership.item_id).filter(not_archived, models.ProjectItem.completed.is_(False)).label('open_count'),
        func.count(ProjectItemMembership.item_id).filter(not_archived, models.ProjectItem.completed.is_(True)).label('completed_count'),
        func.array_agg(distinct(models.ProjectItem.repo)).filter(not_archived, models.ProjectItem.repo.isnot(None)).label('repos'),
    )


def repo_list(aggregated: list[str] | None) -> list[str]:
    """Normalize the repos aggregate, which is NULL for a project with no items."""
    return sorted(aggregated) if aggregated else []


def project_with_counts(project: models.Project, item_count, open_count, completed_count, repos) -> schemas.ProjectWithItemCount:
    """Build the read schema from a project row plus its aggregates.

    One place, because the list and the single-project read return the same
    shape and adding a column to only one of them is the failure mode.
    """
    return schemas.ProjectWithItemCount(
        id=project.id,
        name=project.name,
        description=project.description,
        kind=project.kind,
        status=project.status,
        status_reason=project.status_reason,
        closed_at=project.closed_at,
        position=project.position,
        created_at=project.created_at,
        item_count=item_count,
        open_count=open_count,
        completed_count=completed_count,
        repos=repo_list(repos),
    )


@router.get('/', response_model=list[schemas.ProjectWithItemCount], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    repo: str | None = Query(None, description='Only projects holding at least one item tagged with this repo'),
    project_status: str = Query(
        'active',
        alias='status',
        description="A project status, or 'all'. Terminal projects are hidden by default.",
    ),
):
    if project_status != ALL_STATUSES:
        validate_status(project_status, session)
    query = (
        select(models.Project, *item_count_columns())
        .outerjoin(ProjectItemMembership, models.Project.id == ProjectItemMembership.project_id)
        .outerjoin(models.ProjectItem, ProjectItemMembership.item_id == models.ProjectItem.id)
        .group_by(models.Project.id)
        # closed_at orders the terminal projects, whose position stopped meaning
        # anything the moment they left the running — most recently closed first,
        # since that is the half of a finished list anyone looks at. NULLS FIRST
        # keeps active projects, which have no closed_at, ahead of them in a
        # mixed list, where they fall through to position as before.
        .order_by(models.Project.closed_at.desc().nullsfirst(), models.Project.position.asc())
    )
    if project_status != ALL_STATUSES:
        query = query.where(models.Project.status == project_status)
    if repo is not None:
        # HAVING, not WHERE: filtering the join would also shrink the counts, so
        # a project matching on one item would report only that item.
        query = query.having(func.count(ProjectItemMembership.item_id).filter(models.ProjectItem.repo == repo) > 0)
    return [project_with_counts(*row) for row in session.execute(query).all()]


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


def validate_status(project_status: str, session: Session) -> None:
    """Reject an unknown status here rather than letting the FK raise, as with kind."""
    if session.get(models.ProjectStatus, project_status) is None:
        known = session.scalars(select(models.ProjectStatus.name).order_by(models.ProjectStatus.name)).all()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown project status {project_status!r}. Known statuses: {", ".join(known)}, all',
        )


def require_reason_when_dropped(project_status: str, reason: str | None) -> None:
    """A dropped project without a reason is indistinguishable from a deferred one.

    'Deferred' invites re-proposal; 'dropped, and here is why' closes the
    question. The database CHECK enforces the same rule — this exists so the
    caller gets a 422 naming the flag instead of the constraint's 500.
    """
    if project_status == 'dropped' and not reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Dropping a project requires a reason. Say why it is dropped rather than deferred.',
        )


def ensure_active_name_available(session: Session, name: str, exclude_id: UUID | None = None) -> None:
    """Refuse a name already held by a different ACTIVE project.

    Only active projects hold a name — that is what the partial unique index
    says, and it is what lets a new `clisteno` effort exist after the last one
    was completed. Checked here so the caller gets the conflicting project's id
    rather than the index's IntegrityError.
    """
    query = select(models.Project).where(models.Project.name == name, models.Project.status == 'active')
    if exclude_id is not None:
        query = query.where(models.Project.id != exclude_id)
    if (existing := session.scalars(query).first()) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'An active project named {name!r} already exists ({existing.id}).',
        )


@router.post('/', response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create(project: schemas.ProjectCreate, session: DbSession):
    validate_kind(project.kind, session)
    validate_status(project.status, session)
    require_reason_when_dropped(project.status, project.status_reason)
    if project.status == 'active':
        ensure_active_name_available(session, project.name)

    db_obj = models.Project(**project.model_dump(exclude={'id'}))
    if project.id is not None:
        db_obj.id = project.id
    if db_obj.status in TERMINAL_PROJECT_STATUSES:
        db_obj.closed_at = datetime.now(UTC)
    session.add(db_obj)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Project with id {project.id} already exists') from None
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.ProjectWithItemCount, status_code=status.HTTP_200_OK)
async def read_one(project: ProjectFromPath, session: DbSession):
    counts = (
        select(*item_count_columns())
        .select_from(ProjectItemMembership)
        .outerjoin(models.ProjectItem, ProjectItemMembership.item_id == models.ProjectItem.id)
        .where(ProjectItemMembership.project_id == project.id)
    )
    item_count, open_count, completed_count, repos = session.execute(counts).one()
    return project_with_counts(project, item_count, open_count, completed_count, repos)


def apply_status_transition(project: models.Project, update_data: dict, session: Session) -> None:
    """Fold the derived consequences of a status change into the update payload.

    `closed_at` and the clearing of `status_reason` are consequences of the
    transition, never things a caller sets — a client free to send them could
    leave a project claiming to be active with a closing timestamp on it. This
    is also the one place a transition is validated, which is why status moves
    through PATCH rather than through complete/drop/reopen action endpoints.
    """
    new_status = update_data.get('status')
    reason = update_data.get('status_reason', project.status_reason)

    if new_status is None:
        # No transition, but the reason can still be edited — and cleared, which
        # the CHECK constraint refuses while the project is dropped.
        require_reason_when_dropped(project.status, reason)
        return

    validate_status(new_status, session)
    require_reason_when_dropped(new_status, reason)

    if new_status == 'active':
        update_data['status_reason'] = None
        update_data['closed_at'] = None
    elif new_status != project.status:
        update_data['closed_at'] = datetime.now(UTC)


@router.patch('/{id}/', response_model=schemas.Project, status_code=status.HTTP_200_OK)
async def update(project: ProjectFromPath, update: schemas.ProjectUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('project_update', project_id=project.id, update_data=update_data)
    if (kind := update_data.get('kind')) is not None:
        validate_kind(kind, session)

    # A rename and a reopen both end with the project holding a name as an
    # active project, which is the only status that holds one. Resolving both to
    # the resulting (status, name) checks each of them, and the pair of them, once.
    resulting_status = update_data.get('status', project.status)
    resulting_name = update_data.get('name', project.name)
    if resulting_status == 'active' and (resulting_name != project.name or project.status != 'active'):
        ensure_active_name_available(session, resulting_name, exclude_id=project.id)

    apply_status_transition(project, update_data, session)

    for attr, value in update_data.items():
        setattr(project, attr, value)
    session.commit()
    session.refresh(project)
    return project


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(project: ProjectFromPath, session: DbSession):
    # Find items that only belong to this project (would become orphans)
    multi_project_items = select(ProjectItemMembership.item_id).where(ProjectItemMembership.project_id != project.id)
    orphan_query = (
        select(models.ProjectItem)
        .join(ProjectItemMembership, models.ProjectItem.id == ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == project.id)
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
    project: ProjectFromPath,
    session: DbSession,
    archived: bool = Query(False, description='Include archived items'),
):
    query = (
        select(models.ProjectItem, ProjectItemMembership.position)
        .join(ProjectItemMembership, models.ProjectItem.id == ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == project.id)
    )
    if not archived:
        query = query.where(models.ProjectItem.archived == False)  # noqa: E712

    # position has no unique constraint, so a collision would otherwise order by
    # whatever the database returned
    query = query.order_by(ProjectItemMembership.position.asc(), models.ProjectItem.created_at.asc())

    return [
        schemas.ProjectItemInProject(
            id=item.id,
            number=item.number,
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
