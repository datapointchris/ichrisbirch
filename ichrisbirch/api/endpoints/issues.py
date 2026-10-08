from collections import deque
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import and_
from sqlalchemy import delete as sql_delete
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.api.request_zone import RequestZone
from ichrisbirch.models.issue import CLOSED_ISSUE_STATUSES
from ichrisbirch.models.issue import INITIATIVE_STATUSES
from ichrisbirch.models.issue import ISSUE_PRIORITIES
from ichrisbirch.models.issue import ISSUE_STATUSES
from ichrisbirch.models.issue import ISSUE_TYPES
from ichrisbirch.models.issue import TERMINAL_INITIATIVE_STATUSES
from ichrisbirch.services.date_bounds import apply_date_bounds
from ichrisbirch.services.issue_rank import move_issue
from ichrisbirch.services.issue_rank import rank_at_end
from ichrisbirch.services.issue_readiness import IssueReadiness
from ichrisbirch.services.issue_readiness import measure_readiness
from ichrisbirch.services.issue_refs import resolve_initiative
from ichrisbirch.services.issue_refs import resolve_issue
from ichrisbirch.services.issue_refs import resolve_label
from ichrisbirch.services.issue_refs import resolve_labels
from ichrisbirch.services.issue_views import ISSUE_LOAD_OPTIONS
from ichrisbirch.services.issue_views import calendar_now
from ichrisbirch.services.issue_views import issue_detail
from ichrisbirch.services.issue_views import issue_views
from ichrisbirch.services.issue_views import label_views
from ichrisbirch.services.issue_views import list_order
from ichrisbirch.services.row_limit import RowLimit

logger = structlog.get_logger()
router = APIRouter()

# Not a status, so it is not in the lookup table: `all` is the absence of the
# filter, and storing it would make it assignable to an issue.
ALL_STATUSES = 'all'

# The statuses a new issue may start in. Anything later is reached by working it.
CREATE_STATUSES = ('triage', 'open')


def path_issue(id: str, session: DbSession) -> models.Issue:
    """Resolve the `{id}` segment, which is a UUID or an issue number."""
    return resolve_issue(session, id)


IssueFromPath = Annotated[models.Issue, Depends(path_issue)]


def validate_lookup(session: Session, model, value: str, noun: str, extra: tuple[str, ...] = ()) -> None:
    """Reject an unknown vocabulary value by name rather than letting the foreign key raise."""
    if value in extra or session.get(model, value) is not None:
        return
    known = [*session.scalars(select(model.name).order_by(model.name)).all(), *extra]
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f'Unknown {noun} {value!r}. Known: {", ".join(known)}',
    )


def apply_repo_filter(query: Select, repo: str | None) -> Select:
    """Narrow to one repo; an explicit empty string asks for the issues on no repo."""
    if repo is None:
        return query
    if repo == '':
        return query.where(models.Issue.repo.is_(None))
    return query.where(models.Issue.repo == repo)


def apply_label_filter(query: Select, label: str | None, session: Session) -> Select:
    if label is None:
        return query
    label_row = resolve_label(session, label)
    return query.where(
        models.Issue.id.in_(select(models.IssueLabelAssignment.issue_id).where(models.IssueLabelAssignment.label_id == label_row.id))
    )


def waited_on_by(session: Session, issue_id: UUID) -> list[UUID]:
    """What `issue_id` waits on: the issues it depends on, and its children."""
    dependencies = select(models.IssueDependency.depends_on_id).where(models.IssueDependency.issue_id == issue_id)
    children = select(models.Issue.id).where(models.Issue.parent_id == issue_id)
    return [*session.scalars(dependencies).all(), *session.scalars(children).all()]


def ensure_no_wait_cycle(session: Session, waiter: models.Issue, waited_on: models.Issue) -> None:
    """Refuse a new edge that would leave an issue waiting on itself.

    An issue waits on what it depends on and, as a parent, on its open children.
    A cycle through either kind of edge is a deadlock: nothing in it can become
    ready. The new edge closes one exactly when `waited_on` already reaches
    `waiter`, and the refusal names the path so the caller sees which edge to cut.
    """
    came_from: dict[UUID, UUID | None] = {waited_on.id: None}
    queue = deque([waited_on.id])
    while queue:
        current = queue.popleft()
        if current == waiter.id:
            path: list[UUID] = []
            step: UUID | None = current
            while step is not None:
                path.append(step)
                step = came_from[step]
            numbers = dict(session.execute(select(models.Issue.id, models.Issue.number).where(models.Issue.id.in_(path))).tuples().all())
            chain = ' → '.join(f'#{numbers[i]}' for i in [waiter.id, *reversed(path)])
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'That would leave #{waiter.number} waiting on itself: {chain}',
            )
        for following in waited_on_by(session, current):
            if following not in came_from:
                came_from[following] = current
                queue.append(following)


def ensure_initiative_open(initiative: models.Initiative) -> None:
    if initiative.status in TERMINAL_INITIATIVE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Initiative {initiative.name!r} is {initiative.status}. Reopen it before filing work into it.',
        )


def set_labels(session: Session, issue: models.Issue, slugs: list[str]) -> None:
    """Make the issue's labels exactly `slugs`, keeping the assignment rows that stay."""
    wanted = {label.id for label in resolve_labels(session, slugs)}
    kept = [assignment for assignment in issue.label_assignments if assignment.label_id in wanted]
    held = {assignment.label_id for assignment in kept}
    issue.label_assignments = kept + [models.IssueLabelAssignment(label_id=label_id) for label_id in sorted(wanted - held)]


def clear_claim(issue: models.Issue) -> None:
    issue.claimed_by = None
    issue.claim_expires_ts = None


def unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def resulting_duplicate(session: Session, issue: models.Issue, update_data: dict, target: str) -> UUID | None:
    """The duplicate link the issue ends up with: what was sent, else what it had if it stays canceled."""
    if 'duplicate_of' not in update_data:
        return issue.duplicate_of_id if target == 'canceled' else None
    ref = update_data.pop('duplicate_of')
    if ref is None:
        return None
    if target != 'canceled':
        raise unprocessable('duplicate_of is set only on a canceled issue. Send status canceled with it.')
    duplicate = resolve_issue(session, ref)
    if duplicate.id == issue.id:
        raise unprocessable('An issue cannot duplicate itself')
    return duplicate.id


def resulting_reason(issue: models.Issue, update_data: dict, target: str) -> str | None:
    """The cancel reason the issue ends up with. Only a canceled issue keeps one."""
    if 'status_reason' not in update_data:
        return issue.status_reason if target == 'canceled' else None
    reason = update_data.pop('status_reason')
    if reason is not None and target != 'canceled':
        raise unprocessable('status_reason records why an issue was canceled. Send status canceled with it.')
    return reason


def apply_status_transition(session: Session, issue: models.Issue, update_data: dict, now: datetime) -> None:
    """Validate a status change and apply everything it implies, in one place.

    Closing stamps `closed_ts` and drops the claim. Reopening clears the stamp,
    the reason and any duplicate link. Leaving `in_progress` for anything but a
    close releases the claim. The CHECK constraints refuse each of these states
    too; this exists so a caller gets a 4xx naming the problem.
    """
    new_status = update_data.pop('status', None)
    if new_status is not None:
        validate_lookup(session, models.IssueStatus, new_status, 'issue status')
    target = new_status or issue.status

    duplicate_id = resulting_duplicate(session, issue, update_data, target)
    reason = resulting_reason(issue, update_data, target)
    if target == 'canceled' and not reason and duplicate_id is None:
        raise unprocessable('Canceling an issue requires a reason, or the issue it duplicates.')

    if target == 'completed' and issue.status != 'completed':
        open_children = [child for child in issue.children if not child.is_closed]
        if open_children:
            numbers = ', '.join(f'#{child.number}' for child in open_children)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'#{issue.number} still has open children: {numbers}. Close them first.',
            )

    if target in CLOSED_ISSUE_STATUSES:
        if not issue.is_closed:
            issue.closed_ts = now
        clear_claim(issue)
    else:
        issue.closed_ts = None
        if target != 'in_progress':
            clear_claim(issue)
    issue.status = target
    issue.status_reason = reason
    issue.duplicate_of_id = duplicate_id


def load_issue(session: Session, issue_id: UUID) -> models.Issue:
    issue = session.scalars(select(models.Issue).options(*ISSUE_LOAD_OPTIONS).where(models.Issue.id == issue_id)).one()
    return issue


def detail(session: Session, issue: models.Issue, zone: str) -> schemas.IssueDetail:
    session.expire_all()
    return issue_detail(session, load_issue(session, issue.id), zone)


def single_view(session: Session, issue: models.Issue, zone: str) -> schemas.Issue:
    session.expire_all()
    return issue_views(session, [load_issue(session, issue.id)], zone)[0]


# --- Collections (before /{id}/ so a static segment is never read as an issue) ---


@router.get('/', response_model=list[schemas.Issue], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    zone: RequestZone,
    issue_status: str | None = Query(
        None,
        alias='status',
        description="An issue status, or 'all'. Omitted, every issue not yet completed or canceled.",
    ),
    repo: str | None = Query(None, description='A repo name, or an empty string for issues on no repo'),
    type: str | None = Query(None, description='An issue type'),
    label: str | None = Query(None, description='A label slug'),
    initiative: str | None = Query(None, description='An initiative name or UUID'),
    parent: str | None = Query(None, description='A parent issue number or UUID: its children'),
    priority: int | None = Query(None, ge=0, le=4, description="The issue's own priority"),
    claimed_by: str | None = Query(None, description='Issues held by this claimant'),
    search: str | None = Query(None, description='Text to find in the title or description'),
    blocked: bool | None = Query(None, description='True for issues waiting on an unclosed dependency, false for the rest'),
    start_date: str | None = None,
    end_date: str | None = None,
    limit: RowLimit = None,
):
    """List issues, open work first by effective priority then rank, closed work after it.

    Completed and canceled issues accumulate without bound, so the default leaves
    them out. The date bounds narrow on `closed_ts`, the one date that records an
    issue finishing rather than being edited. Blocked is derived on every read,
    so it narrows after the query and before the limit.
    """
    query = select(models.Issue).options(*ISSUE_LOAD_OPTIONS)
    if issue_status is None:
        query = query.where(models.Issue.status.not_in(CLOSED_ISSUE_STATUSES))
    elif issue_status != ALL_STATUSES:
        validate_lookup(session, models.IssueStatus, issue_status, 'issue status', extra=(ALL_STATUSES,))
        query = query.where(models.Issue.status == issue_status)
    if type is not None:
        validate_lookup(session, models.IssueType, type, 'issue type')
        query = query.where(models.Issue.type == type)
    if initiative is not None:
        query = query.where(models.Issue.initiative_id == resolve_initiative(session, initiative).id)
    if parent is not None:
        query = query.where(models.Issue.parent_id == resolve_issue(session, parent).id)
    if priority is not None:
        query = query.where(models.Issue.priority == priority)
    if claimed_by is not None:
        query = query.where(models.Issue.claimed_by == claimed_by)
    if search:
        pattern = f'%{search}%'
        query = query.where(or_(models.Issue.title.ilike(pattern), models.Issue.description.ilike(pattern)))
    query = apply_repo_filter(query, repo)
    query = apply_label_filter(query, label, session)
    query = apply_date_bounds(query, models.Issue.closed_ts, start_date, end_date, timezone=zone)

    today, now = calendar_now(zone)
    readiness = measure_readiness(session, today, now)
    issues = sorted(session.scalars(query).all(), key=list_order(readiness))
    if blocked is not None:
        issues = [issue for issue in issues if (issue.id in readiness.blocked) == blocked]
    if limit is not None:
        issues = issues[:limit]
    return issue_views(session, issues, zone, readiness)


def ready_issues(
    session: Session,
    zone: str,
    *,
    repo: str | None,
    type: str | None,
    label: str | None,
    initiative: str | UUID | None,
) -> tuple[list[models.Issue], IssueReadiness]:
    """The ready queue in the order it is taken, and the readiness it was cut from.

    Decisions wait on a person, so the queue leaves them out unless `type` asks
    for them by name.
    """
    today, now = calendar_now(zone)
    readiness = measure_readiness(session, today, now)
    query = select(models.Issue).options(*ISSUE_LOAD_OPTIONS).where(models.Issue.id.in_(readiness.ready))
    if type is not None:
        validate_lookup(session, models.IssueType, type, 'issue type')
        query = query.where(models.Issue.type == type)
    else:
        query = query.where(models.Issue.type != 'decision')
    if initiative is not None:
        query = query.where(models.Issue.initiative_id == resolve_initiative(session, initiative).id)
    query = apply_repo_filter(query, repo)
    query = apply_label_filter(query, label, session)
    return sorted(session.scalars(query).all(), key=readiness.sort_key), readiness


@router.get('/ready/', response_model=list[schemas.Issue], status_code=status.HTTP_200_OK)
async def read_ready(
    session: DbSession,
    zone: RequestZone,
    repo: str | None = Query(None, description='A repo name, or an empty string for issues on no repo'),
    type: str | None = Query(None, description='An issue type. Decisions are left out unless asked for here.'),
    label: str | None = Query(None, description='A label slug'),
    initiative: str | None = Query(None, description='An initiative name or UUID'),
    limit: RowLimit = None,
):
    """The issues an agent could take now, in the order to take them; the first row is next."""
    issues, readiness = ready_issues(session, zone, repo=repo, type=type, label=label, initiative=initiative)
    if limit is not None:
        issues = issues[:limit]
    return issue_views(session, issues, zone, readiness)


def claim_values(claimant: str, minutes: int, now: datetime) -> dict:
    return {
        'status': 'in_progress',
        'claimed_by': claimant,
        'claim_expires_ts': now + timedelta(minutes=minutes),
        'updated_ts': now,
    }


def claimable(now: datetime, claimant: str | None = None):
    """The compare half of the claim's compare-and-set: no live claim by anyone else."""
    free = or_(
        models.Issue.status == 'open',
        and_(models.Issue.status == 'in_progress', models.Issue.claim_expires_ts.is_not(None), models.Issue.claim_expires_ts <= now),
    )
    if claimant is None:
        return free
    return or_(free, and_(models.Issue.status == 'in_progress', models.Issue.claimed_by == claimant))


@router.post('/ready/claim/', response_model=schemas.IssueClaimResult, status_code=status.HTTP_200_OK)
async def claim_next(request: schemas.IssueReadyClaimRequest, session: DbSession, zone: RequestZone):
    """Take the head of the ready queue in one step.

    Each candidate is taken with a compare-and-set, so two agents asking at once
    never hold the same issue: the loser's update matches no row and it moves on
    to the next candidate.
    """
    issues, _ = ready_issues(session, zone, repo=request.repo, type=request.type, label=request.label, initiative=request.initiative)
    now = datetime.now(UTC)
    for candidate in issues:
        taken = session.execute(
            sql_update(models.Issue)
            .where(models.Issue.id == candidate.id, claimable(now))
            .values(**claim_values(request.claimant, request.minutes, now))
            .returning(models.Issue.id),
            execution_options={'synchronize_session': False},
        ).scalar_one_or_none()
        if taken is not None:
            session.commit()
            logger.info('issue_claimed', number=candidate.number, claimant=request.claimant)
            return schemas.IssueClaimResult(issue=single_view(session, candidate, zone))
    return schemas.IssueClaimResult(issue=None)


@router.get('/vocabulary/', response_model=schemas.IssueVocabulary, status_code=status.HTTP_200_OK)
async def read_vocabulary(session: DbSession):
    """Every value the closed issue fields accept, with the open issue count per label.

    Statuses and types come back in their lifecycle order rather than the
    table's, so a client can render them as given.
    """
    statuses = set(session.scalars(select(models.IssueStatus.name)).all())
    types = set(session.scalars(select(models.IssueType.name)).all())
    initiative_statuses = set(session.scalars(select(models.InitiativeStatus.name)).all())
    return schemas.IssueVocabulary(
        statuses=in_declared_order(statuses, ISSUE_STATUSES),
        types=in_declared_order(types, ISSUE_TYPES),
        priorities=[schemas.IssuePriorityName(value=value, name=name) for value, name in ISSUE_PRIORITIES.items()],
        initiative_statuses=in_declared_order(initiative_statuses, INITIATIVE_STATUSES),
        labels=label_views(session),
    )


def in_declared_order(values: set[str], declared: list[str]) -> list[str]:
    """The declared values first in their order, then any the table holds beyond them."""
    return [v for v in declared if v in values] + sorted(values - set(declared))


# --- One issue ---


@router.post('/', response_model=schemas.IssueDetail, status_code=status.HTTP_201_CREATED)
async def create(issue: schemas.IssueCreate, session: DbSession, zone: RequestZone):
    if issue.status not in CREATE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'A new issue starts as {" or ".join(CREATE_STATUSES)}, not {issue.status!r}',
        )
    validate_lookup(session, models.IssueType, issue.type, 'issue type')

    db_issue = models.Issue(
        title=issue.title,
        description=issue.description,
        acceptance=issue.acceptance,
        repo=issue.repo,
        type=issue.type,
        status=issue.status,
        priority=issue.priority,
        deferred_until_date=issue.deferred_until_date,
        rank=rank_at_end(session),
    )
    if issue.initiative is not None:
        initiative = resolve_initiative(session, issue.initiative)
        ensure_initiative_open(initiative)
        db_issue.initiative_id = initiative.id
    if issue.parent is not None:
        db_issue.parent_id = resolve_issue(session, issue.parent).id
    if issue.discovered_from is not None:
        db_issue.discovered_from_id = resolve_issue(session, issue.discovered_from).id
    depends_on = [resolve_issue(session, ref) for ref in dict.fromkeys(issue.depends_on)]
    session.add(db_issue)
    set_labels(session, db_issue, issue.labels)
    session.flush()
    # Only through the parent can a brand-new issue close a cycle: depending on
    # its own parent, or on anything that waits on that parent.
    for blocker in depends_on:
        ensure_no_wait_cycle(session, db_issue, blocker)
        session.add(models.IssueDependency(issue_id=db_issue.id, depends_on_id=blocker.id))
        session.flush()
    session.commit()
    logger.info('issue_created', number=db_issue.number, repo=db_issue.repo)
    return detail(session, db_issue, zone)


@router.get('/{id}/', response_model=schemas.IssueDetail, status_code=status.HTTP_200_OK)
async def read_one(issue: IssueFromPath, session: DbSession, zone: RequestZone):
    return detail(session, issue, zone)


@router.patch('/{id}/', response_model=schemas.IssueDetail, status_code=status.HTTP_200_OK)
async def update(issue: IssueFromPath, update: schemas.IssueUpdate, session: DbSession, zone: RequestZone):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('issue_update', number=issue.number, fields=sorted(update_data))
    now = datetime.now(UTC)

    if (issue_type := update_data.get('type')) is not None:
        validate_lookup(session, models.IssueType, issue_type, 'issue type')
    if 'initiative' in update_data:
        ref = update_data.pop('initiative')
        if ref is None:
            issue.initiative_id = None
        else:
            initiative = resolve_initiative(session, ref)
            if initiative.id != issue.initiative_id:
                ensure_initiative_open(initiative)
            issue.initiative_id = initiative.id
    if 'parent' in update_data:
        ref = update_data.pop('parent')
        if ref is None:
            issue.parent_id = None
        else:
            parent = resolve_issue(session, ref)
            if parent.id != issue.parent_id:
                ensure_no_wait_cycle(session, parent, issue)
            issue.parent_id = parent.id
    if 'discovered_from' in update_data:
        ref = update_data.pop('discovered_from')
        issue.discovered_from_id = None if ref is None else resolve_issue(session, ref).id
    if 'labels' in update_data:
        set_labels(session, issue, update_data.pop('labels'))

    apply_status_transition(session, issue, update_data, now)

    for attr, value in update_data.items():
        setattr(issue, attr, value)
    issue.updated_ts = now
    session.commit()
    return detail(session, issue, zone)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(issue: IssueFromPath, session: DbSession):
    session.delete(issue)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Claim ---


def claim_conflict(issue: models.Issue) -> str:
    """Name who holds the issue, so the refused agent can tell whether to wait or move on."""
    if issue.claimed_by is None or issue.claim_expires_ts is None:
        # Moved to in_progress by hand, which is a person working it.
        return f'#{issue.number} is in progress without a claim. Release it to open before claiming it.'
    until = issue.claim_expires_ts.astimezone(UTC)
    return f'#{issue.number} is claimed by {issue.claimed_by} until {until:%Y-%m-%d %H:%M} UTC'


@router.post('/{id}/claim/', response_model=schemas.Issue, status_code=status.HTTP_200_OK)
async def claim(issue: IssueFromPath, request: schemas.IssueClaimRequest, session: DbSession, zone: RequestZone):
    """Take this issue, or extend the claim already held under the same name.

    A blocked issue is refused: its blockers are what to take instead.
    """
    if issue.is_closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'#{issue.number} is {issue.status}')
    if issue.status == 'triage':
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'#{issue.number} is in triage. Accept it as open before claiming it.',
        )
    blockers = [edge.depends_on for edge in issue.dependencies if not edge.depends_on.is_closed]
    if blockers:
        numbers = ', '.join(f'#{b.number}' for b in sorted(blockers, key=lambda b: b.number))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'#{issue.number} is blocked by {numbers}')

    now = datetime.now(UTC)
    taken = session.execute(
        sql_update(models.Issue)
        .where(models.Issue.id == issue.id, claimable(now, request.claimant))
        .values(**claim_values(request.claimant, request.minutes, now))
        .returning(models.Issue.id),
        execution_options={'synchronize_session': False},
    ).scalar_one_or_none()
    if taken is None:
        session.rollback()
        session.refresh(issue)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=claim_conflict(issue))
    session.commit()
    logger.info('issue_claimed', number=issue.number, claimant=request.claimant)
    return single_view(session, issue, zone)


@router.delete('/{id}/claim/', response_model=schemas.Issue, status_code=status.HTTP_200_OK)
async def release(issue: IssueFromPath, session: DbSession, zone: RequestZone):
    """Give the issue back to the ready queue. Releasing an issue not in progress changes nothing.

    A claim sits only on an in-progress issue, so this one test covers both a
    claim and work a person moved to in progress by hand.
    """
    if issue.status == 'in_progress':
        clear_claim(issue)
        issue.status = 'open'
        issue.updated_ts = datetime.now(UTC)
        session.commit()
    return single_view(session, issue, zone)


# --- Rank ---


@router.post('/{id}/rank/', response_model=schemas.Issue, status_code=status.HTTP_200_OK)
async def rank(issue: IssueFromPath, move: schemas.IssueRankMove, session: DbSession, zone: RequestZone):
    """Place this issue directly before or after another in the global order."""
    before = resolve_issue(session, move.before) if move.before is not None else None
    after = resolve_issue(session, move.after) if move.after is not None else None
    if any(neighbor is not None and neighbor.id == issue.id for neighbor in (before, after)):
        raise unprocessable('An issue cannot be ranked beside itself')
    move_issue(session, issue, before=before, after=after)
    session.commit()
    return single_view(session, issue, zone)


# --- Dependencies ---


@router.post('/{id}/dependencies/', response_model=schemas.IssueDetail, status_code=status.HTTP_201_CREATED)
async def add_dependency(issue: IssueFromPath, dependency: schemas.IssueDependencyCreate, session: DbSession, zone: RequestZone):
    depends_on = resolve_issue(session, dependency.depends_on)
    if depends_on.id == issue.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='An issue cannot depend on itself')
    if session.get(models.IssueDependency, (issue.id, depends_on.id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'#{issue.number} already depends on #{depends_on.number}',
        )
    ensure_no_wait_cycle(session, issue, depends_on)
    session.add(models.IssueDependency(issue_id=issue.id, depends_on_id=depends_on.id))
    issue.updated_ts = datetime.now(UTC)
    session.commit()
    return detail(session, issue, zone)


def path_dependency(dep_id: str, session: DbSession) -> models.Issue:
    return resolve_issue(session, dep_id)


@router.delete('/{id}/dependencies/{dep_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def remove_dependency(issue: IssueFromPath, depends_on: Annotated[models.Issue, Depends(path_dependency)], session: DbSession):
    edge = session.get(models.IssueDependency, (issue.id, depends_on.id))
    if edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'#{issue.number} does not depend on #{depends_on.number}',
        )
    session.delete(edge)
    issue.updated_ts = datetime.now(UTC)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Comments ---


@router.get('/{id}/comments/', response_model=list[schemas.IssueComment], status_code=status.HTTP_200_OK)
async def read_comments(issue: IssueFromPath, session: DbSession, limit: RowLimit = None):
    """The issue's comments, oldest first, so a thread reads in the order it was written."""
    query = (
        select(models.IssueComment)
        .where(models.IssueComment.issue_id == issue.id)
        .order_by(models.IssueComment.created_ts, models.IssueComment.id)
    )
    if limit is not None:
        query = query.limit(limit)
    return list(session.scalars(query).all())


@router.post('/{id}/comments/', response_model=schemas.IssueComment, status_code=status.HTTP_201_CREATED)
async def create_comment(issue: IssueFromPath, comment: schemas.IssueCommentCreate, session: DbSession):
    db_comment = models.IssueComment(issue_id=issue.id, body=comment.body, author=comment.author)
    session.add(db_comment)
    issue.updated_ts = datetime.now(UTC)
    session.commit()
    session.refresh(db_comment)
    return db_comment


@router.delete('/{id}/comments/{comment_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(issue: IssueFromPath, comment_id: UUID, session: DbSession):
    deleted = session.execute(
        sql_delete(models.IssueComment)
        .where(models.IssueComment.id == comment_id, models.IssueComment.issue_id == issue.id)
        .returning(models.IssueComment.id)
    ).scalar_one_or_none()
    if deleted is None:
        raise NotFoundException('comment', str(comment_id), logger)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
