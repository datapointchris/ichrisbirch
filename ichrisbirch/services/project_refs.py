"""Resolve the references a person or an agent actually types.

An item's key is a UUID and its handle is a short number; a project's key is a
UUID and its handle is its unique name. Every endpoint that takes one takes
either, resolved here inside the request that was going to hit the database
anyway. Doing it client-side instead would mean a lookup request per reference
just to translate what the previous command printed back into a key.

The two forms are distinguishable without ambiguity: a UUID parses as one, a
number is all digits, and a project name is neither. Nothing guesses.
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


def _item_by_number(session: Session, number: int) -> models.ProjectItem | None:
    return session.scalar(select(models.ProjectItem).where(models.ProjectItem.number == number))


def resolve_item(session: Session, ref: str | UUID | int) -> models.ProjectItem:
    """Fetch a project item by its UUID or its number."""
    item: models.ProjectItem | None
    if isinstance(ref, int):
        item = _item_by_number(session, ref)
    elif isinstance(ref, UUID):
        item = session.get(models.ProjectItem, ref)
    # A hyphenless UUID can be 32 decimal digits, so it is parsed before the
    # all-digits test. No number will ever be that long.
    elif (item_id := _parse_uuid(ref)) is not None:
        item = session.get(models.ProjectItem, item_id)
    elif ref.isdigit():
        item = _item_by_number(session, int(ref))
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'{ref!r} is not a project item UUID or number',
        )
    if item is None:
        raise NotFoundException('project_item', str(ref), logger)
    return item


def resolve_project(session: Session, ref: str | UUID) -> models.Project:
    """Fetch a project by its UUID or its name.

    Projects get no number: `name` is already unique and is what anyone types.
    """
    project: models.Project | None
    if isinstance(ref, UUID):
        project = session.get(models.Project, ref)
    elif (project_id := _parse_uuid(ref)) is not None:
        project = session.get(models.Project, project_id)
    else:
        project = session.scalar(select(models.Project).where(models.Project.name == ref))
    if project is None:
        raise NotFoundException('project', str(ref), logger)
    return project
