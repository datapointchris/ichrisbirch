"""Resolve a shopping section or item from its UUID or its name.

Both are unique on the case-folded name, so a name is what anyone types and
there is no number beside the key. A miss names the nearest names, since a name
matches only in full.
"""

from uuid import UUID

import structlog
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.services.names_near import names_near

logger = structlog.get_logger()


def _parse_uuid(ref: str) -> UUID | None:
    try:
        return UUID(ref)
    except ValueError:
        return None


def section_by_name(session: Session, name: str) -> models.ShoppingSection | None:
    return session.scalar(select(models.ShoppingSection).where(func.lower(models.ShoppingSection.name) == name.strip().lower()))


def item_by_name(session: Session, name: str) -> models.ShoppingItem | None:
    return session.scalar(select(models.ShoppingItem).where(func.lower(models.ShoppingItem.name) == name.strip().lower()))


def resolve_section(session: Session, ref: str | UUID) -> models.ShoppingSection:
    key = ref if isinstance(ref, UUID) else _parse_uuid(ref)
    section = session.get(models.ShoppingSection, key) if key is not None else section_by_name(session, str(ref))
    if section is None:
        names = session.scalars(select(models.ShoppingSection.name).order_by(models.ShoppingSection.rank)).all()
        near = names_near(str(ref), names) if key is None else []
        raise NotFoundException('shopping section', str(ref), logger, near=near)
    return section


def resolve_item(session: Session, ref: str | UUID) -> models.ShoppingItem:
    key = ref if isinstance(ref, UUID) else _parse_uuid(ref)
    item = session.get(models.ShoppingItem, key) if key is not None else item_by_name(session, str(ref))
    if item is None:
        names = session.scalars(
            select(models.ShoppingItem.name).order_by(models.ShoppingItem.is_needed.desc(), models.ShoppingItem.name)
        ).all()
        near = names_near(str(ref), names) if key is None else []
        raise NotFoundException('shopping item', str(ref), logger, near=near)
    return item
