"""Resolve the references a person or an agent types for issues, initiatives and labels.

An issue answers to its UUID or its number, an initiative to its UUID or its
name, and a label to its slug. Each endpoint resolves what it was given inside
the request that was going to reach the database anyway.
"""

from uuid import UUID

import structlog
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.exceptions import NotFoundException

logger = structlog.get_logger()


def _parse_uuid(ref: str) -> UUID | None:
    try:
        return UUID(ref)
    except ValueError:
        return None


def _issue_by_number(session: Session, number: int) -> models.Issue | None:
    return session.scalar(select(models.Issue).where(models.Issue.number == number))


def resolve_issue(session: Session, ref: str | UUID | int) -> models.Issue:
    """Fetch an issue by its UUID or its number."""
    issue: models.Issue | None
    if isinstance(ref, int):
        issue = _issue_by_number(session, ref)
    elif isinstance(ref, UUID):
        issue = session.get(models.Issue, ref)
    # A hyphenless UUID can be 32 decimal digits, so it is parsed before the
    # all-digits test. No number will ever be that long.
    elif (issue_id := _parse_uuid(ref)) is not None:
        issue = session.get(models.Issue, issue_id)
    elif ref.lstrip('#').isdigit():
        issue = _issue_by_number(session, int(ref.lstrip('#')))
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'{ref!r} is not an issue UUID or number',
        )
    if issue is None:
        raise NotFoundException('issue', str(ref), logger)
    return issue


def _initiative_by_name(session: Session, name: str) -> models.Initiative | None:
    """The active initiative holding the name, else a lone closed one, else ambiguity named."""
    matches = session.scalars(select(models.Initiative).where(models.Initiative.name == name)).all()
    active = [initiative for initiative in matches if initiative.status == 'active']
    if active:
        return active[0]
    if len(matches) == 1:
        return matches[0]
    if matches:
        candidates = ', '.join(f'{initiative.id} ({initiative.status})' for initiative in sorted(matches, key=lambda i: i.status))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'{name!r} names {len(matches)} closed initiatives and no active one. Use an id: {candidates}',
        )
    return None


def resolve_initiative(session: Session, ref: str | UUID) -> models.Initiative:
    """Fetch an initiative by its UUID or its name."""
    initiative: models.Initiative | None
    if isinstance(ref, UUID):
        initiative = session.get(models.Initiative, ref)
    elif (initiative_id := _parse_uuid(ref)) is not None:
        initiative = session.get(models.Initiative, initiative_id)
    else:
        initiative = _initiative_by_name(session, ref)
    if initiative is None:
        raise NotFoundException('initiative', str(ref), logger)
    return initiative


def resolve_label(session: Session, slug: str) -> models.IssueLabel:
    label = session.scalar(select(models.IssueLabel).where(models.IssueLabel.slug == slug))
    if label is None:
        raise NotFoundException('label', slug, logger)
    return label


def resolve_labels(session: Session, slugs: list[str]) -> list[models.IssueLabel]:
    """Fetch every named label, refusing the set if any is unknown or two share a group.

    The vocabulary is closed, so an unknown slug is a typo or a label nobody has
    defined yet, and either way it is named rather than created. Labels in one
    group exclude each other, which is the whole meaning of a group.
    """
    wanted = list(dict.fromkeys(slugs))
    found = {label.slug: label for label in session.scalars(select(models.IssueLabel).where(models.IssueLabel.slug.in_(wanted)))}
    unknown = [slug for slug in wanted if slug not in found]
    if unknown:
        known = session.scalars(select(models.IssueLabel.slug).order_by(models.IssueLabel.slug)).all()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown label {", ".join(unknown)}. Known labels: {", ".join(known) or "none yet"}',
        )
    labels = [found[slug] for slug in wanted]
    by_group: dict[str, list[str]] = {}
    for label in labels:
        if label.group_slug is not None:
            by_group.setdefault(label.group_slug, []).append(label.slug)
    clashes = {group: members for group, members in by_group.items() if len(members) > 1}
    if clashes:
        described = '; '.join(f'{group}: {", ".join(members)}' for group, members in sorted(clashes.items()))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'An issue takes one label per group. Conflicting: {described}',
        )
    return labels
