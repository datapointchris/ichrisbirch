"""The shopping list: sections, the item catalog, and the purchase log.

What the catalog is and why order is a fractional rank is `models/shopping.py`.
A section or an item in a path answers to its UUID or its name.
"""

import datetime as dt
from typing import Annotated
from uuid import UUID

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
from sqlalchemy.orm import contains_eager

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.api.request_zone import RequestZone
from ichrisbirch.schemas.shopping import SHOPPING_ITEM_STATUSES
from ichrisbirch.schemas.shopping import ShoppingSectionRef
from ichrisbirch.services.date_bounds import apply_date_bounds
from ichrisbirch.services.fractional_rank import move_ranked
from ichrisbirch.services.fractional_rank import rank_at_end
from ichrisbirch.services.row_limit import CappedRowLimit
from ichrisbirch.services.row_limit import RowLimit
from ichrisbirch.services.row_limit import apply_row_limit
from ichrisbirch.services.shopping_refs import item_by_name
from ichrisbirch.services.shopping_refs import resolve_item
from ichrisbirch.services.shopping_refs import resolve_section
from ichrisbirch.services.shopping_refs import section_by_name

logger = structlog.get_logger()
router = APIRouter()

NOTE_SEPARATOR = '; '
# The purchase log only grows, so a read with no limit takes the newest of it.
PURCHASES_SHOWN = 100


def path_section(id: str, session: DbSession) -> models.ShoppingSection:
    """Resolve the `{id}` segment, which is a UUID or a section name."""
    return resolve_section(session, id)


def path_item(id: str, session: DbSession) -> models.ShoppingItem:
    """Resolve the `{id}` segment, which is a UUID or an item name."""
    return resolve_item(session, id)


SectionFromPath = Annotated[models.ShoppingSection, Depends(path_section)]
ItemFromPath = Annotated[models.ShoppingItem, Depends(path_item)]


def unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def refuse_taken_section_name(session: Session, name: str, exclude_id: UUID | None = None) -> None:
    """A 409 naming the holder, rather than the unique index failing as a 500."""
    holder = section_by_name(session, name)
    if holder is not None and holder.id != exclude_id:
        raise conflict(f'A section named {holder.name!r} already exists')


def refuse_taken_item_name(session: Session, name: str, exclude_id: UUID | None = None) -> None:
    holder = item_by_name(session, name)
    if holder is not None and holder.id != exclude_id:
        raise conflict(f'{holder.name!r} is already in the catalog. Add it by that name to put it on the list.')


def section_or_unsorted(session: Session, ref: ShoppingSectionRef | None) -> models.ShoppingSection | None:
    return resolve_section(session, ref) if ref is not None else None


def joined_note(existing: str | None, added: str | None) -> str | None:
    """Add a note to the one an item already carries, once."""
    if not added:
        return existing
    if not existing:
        return added
    if added in existing.split(NOTE_SEPARATOR):
        return existing
    return f'{existing}{NOTE_SEPARATOR}{added}'


def move_to_section(session: Session, item: models.ShoppingItem, section: models.ShoppingSection | None) -> None:
    """Move an item into a section at its end. Staying put keeps its place."""
    if (section.id if section else None) == item.section_id:
        return
    item.section = section
    item.rank = rank_at_end(session, models.ShoppingItem)


def purchase_stats(session: Session, item_ids: list[UUID]) -> dict[UUID, tuple[int, dt.datetime | None]]:
    if not item_ids:
        return {}
    purchases = models.ShoppingPurchase
    rows = session.execute(
        select(purchases.item_id, func.count(purchases.id), func.max(purchases.purchased_ts))
        .where(purchases.item_id.in_(item_ids))
        .group_by(purchases.item_id)
    ).all()
    return {item_id: (count, last) for item_id, count, last in rows if item_id is not None}


def item_views(session: Session, items: list[models.ShoppingItem]) -> list[schemas.ShoppingItem]:
    stats = purchase_stats(session, [item.id for item in items])
    views = []
    for item in items:
        count, last = stats.get(item.id, (0, None))
        views.append(
            schemas.ShoppingItem(
                id=item.id,
                name=item.name,
                note=item.note,
                section_id=item.section_id,
                section_name=item.section.name if item.section else None,
                rank=item.rank,
                is_needed=item.is_needed,
                needed_ts=item.needed_ts,
                created_ts=item.created_ts,
                purchase_count=count,
                last_purchased_ts=last,
            )
        )
    return views


def item_view(session: Session, item: models.ShoppingItem) -> schemas.ShoppingItem:
    session.refresh(item)
    return item_views(session, [item])[0]


# --- Sections ---------------------------------------------------------------


@router.get('/sections/', response_model=list[schemas.ShoppingSection], status_code=status.HTTP_200_OK)
def read_sections(session: DbSession, limit: RowLimit = None):
    """Every section in list order. Unsorted is not a row, so it is not listed."""
    query = select(models.ShoppingSection).order_by(models.ShoppingSection.rank)
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.post('/sections/', response_model=schemas.ShoppingSection, status_code=status.HTTP_201_CREATED)
def create_section(section: schemas.ShoppingSectionCreate, session: DbSession):
    refuse_taken_section_name(session, section.name)
    created = models.ShoppingSection(name=section.name, rank=rank_at_end(session, models.ShoppingSection))
    session.add(created)
    session.commit()
    session.refresh(created)
    logger.info('shopping_section_created', name=created.name)
    return created


@router.patch('/sections/{id}/', response_model=schemas.ShoppingSection, status_code=status.HTTP_200_OK)
def update_section(section: SectionFromPath, update: schemas.ShoppingSectionUpdate, session: DbSession):
    data = update.model_dump(exclude_unset=True)
    if 'name' in data:
        refuse_taken_section_name(session, data['name'], exclude_id=section.id)
        logger.info('shopping_section_renamed', old=section.name, new=data['name'])
        section.name = data['name']
    session.commit()
    session.refresh(section)
    return section


@router.delete('/sections/{id}/', status_code=status.HTTP_204_NO_CONTENT)
def delete_section(section: SectionFromPath, session: DbSession):
    """Delete a section. Its items, on the list or off it, fall to Unsorted."""
    logger.info('shopping_section_deleted', name=section.name)
    session.delete(section)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/sections/{id}/rank/', response_model=schemas.ShoppingSection, status_code=status.HTTP_200_OK)
def rank_section(section: SectionFromPath, move: schemas.ShoppingSectionRankMove, session: DbSession):
    """Place this section directly before or after another."""
    before = resolve_section(session, move.before) if move.before is not None else None
    after = resolve_section(session, move.after) if move.after is not None else None
    if any(neighbor is not None and neighbor.id == section.id for neighbor in (before, after)):
        raise unprocessable('A section cannot be placed beside itself')
    move_ranked(session, section, before=before, after=after)
    session.commit()
    session.refresh(section)
    return section


# --- Items ------------------------------------------------------------------


@router.get('/items/', response_model=list[schemas.ShoppingItem], status_code=status.HTTP_200_OK)
def read_items(
    session: DbSession,
    limit: RowLimit = None,
    item_status: str = Query(
        'needed',
        alias='status',
        description='needed is on the list, stocked is off it, all is the whole catalog.',
    ),
    section: str | None = Query(None, description='Only items in this section, by UUID or name.'),
    q: str | None = Query(None, description='Only items whose name contains this, names starting with it first.'),
):
    """List items in list order: section by section, Unsorted first, each in its rank.

    `needed` is the default because the catalog only grows. `q` reorders by
    name, prefix matches first, because it is how a box offers completions.
    """
    if item_status not in SHOPPING_ITEM_STATUSES:
        raise unprocessable(f'Unknown status {item_status!r}. Known statuses: {", ".join(SHOPPING_ITEM_STATUSES)}')

    items = models.ShoppingItem
    query = select(items).outerjoin(items.section).options(contains_eager(items.section))
    if item_status == 'needed':
        query = query.where(items.is_needed.is_(True))
    elif item_status == 'stocked':
        query = query.where(items.is_needed.is_(False))
    if section is not None:
        query = query.where(items.section_id == resolve_section(session, section).id)

    folded = q.strip().lower() if q else ''
    if folded:
        name = func.lower(items.name)
        query = query.where(name.contains(folded, autoescape=True)).order_by(name.startswith(folded, autoescape=True).desc(), name)
    else:
        query = query.order_by(models.ShoppingSection.rank.asc().nulls_first(), items.rank)

    return item_views(session, list(session.scalars(apply_row_limit(query, limit)).all()))


@router.post('/items/', response_model=schemas.ShoppingItem, status_code=status.HTTP_201_CREATED)
def add_item(new: schemas.ShoppingItemCreate, response: Response, session: DbSession):
    """Put a name on the list. A new name is created (201); a known one is listed again (200).

    A known item returns to the section and place it held, unless `section` is
    sent, where it goes last; a null `section` is Unsorted. A note given while
    the item is already on the list is added to the one it carries.
    """
    section = section_or_unsorted(session, new.section)
    item = item_by_name(session, new.name)
    now = dt.datetime.now(dt.UTC)

    if item is None:
        item = models.ShoppingItem(
            name=new.name,
            note=new.note,
            section=section,
            rank=rank_at_end(session, models.ShoppingItem),
            is_needed=True,
            needed_ts=now,
        )
        session.add(item)
        session.commit()
        logger.info('shopping_item_created', name=item.name)
        return item_view(session, item)

    response.status_code = status.HTTP_200_OK
    if item.is_needed:
        item.note = joined_note(item.note, new.note)
    else:
        item.is_needed = True
        item.needed_ts = now
        if new.note:
            item.note = new.note
    if 'section' in new.model_fields_set:
        move_to_section(session, item, section)
    session.commit()
    logger.info('shopping_item_listed', name=item.name)
    return item_view(session, item)


@router.get('/items/{id}/', response_model=schemas.ShoppingItem, status_code=status.HTTP_200_OK)
def read_item(item: ItemFromPath, session: DbSession):
    return item_views(session, [item])[0]


@router.patch('/items/{id}/', response_model=schemas.ShoppingItem, status_code=status.HTTP_200_OK)
def update_item(item: ItemFromPath, update: schemas.ShoppingItemUpdate, session: DbSession):
    data = update.model_dump(exclude_unset=True)
    if 'name' in data:
        refuse_taken_item_name(session, data['name'], exclude_id=item.id)
        item.name = data['name']
    if 'note' in data:
        item.note = data['note'] or None
    if 'section' in data:
        move_to_section(session, item, section_or_unsorted(session, data['section']))
    if 'is_needed' in data:
        if data['is_needed'] and not item.is_needed:
            item.needed_ts = dt.datetime.now(dt.UTC)
        item.is_needed = data['is_needed']
    session.commit()
    return item_view(session, item)


@router.delete('/items/{id}/', status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item: ItemFromPath, session: DbSession):
    """Forget an item. Its purchases stay in the log under the name they were bought as."""
    logger.info('shopping_item_deleted', name=item.name)
    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/items/{id}/rank/', response_model=schemas.ShoppingItem, status_code=status.HTTP_200_OK)
def rank_item(item: ItemFromPath, move: schemas.ShoppingItemRankMove, session: DbSession):
    """Move an item into a section, directly before or after a neighbor there, or last."""
    section = section_or_unsorted(session, move.section)
    before = resolve_item(session, move.before) if move.before is not None else None
    after = resolve_item(session, move.after) if move.after is not None else None
    neighbor = before or after
    if neighbor is not None:
        if neighbor.id == item.id:
            raise unprocessable('An item cannot be placed beside itself')
        target_id = section.id if section else None
        if neighbor.section_id != target_id:
            where = repr(neighbor.section.name) if neighbor.section else 'Unsorted'
            raise unprocessable(f'{neighbor.name!r} is in {where}, so it cannot place an item in another section')

    item.section = section
    if neighbor is None:
        item.rank = rank_at_end(session, models.ShoppingItem)
    else:
        move_ranked(session, item, before=before, after=after)
    session.commit()
    return item_view(session, item)


@router.post('/items/{id}/purchases/', response_model=schemas.ShoppingPurchase, status_code=status.HTTP_201_CREATED)
def check_off(item: ItemFromPath, session: DbSession):
    """Record buying an item, which takes it off the list.

    The purchase keeps the note, and the item gives it up: a note is for one
    trip. Deleting the purchase hands it back.
    """
    if not item.is_needed:
        raise conflict(f'{item.name!r} is not on the list. Add it before checking it off.')
    purchase = models.ShoppingPurchase(
        item=item,
        item_name=item.name,
        note=item.note,
        section_name=item.section.name if item.section else None,
    )
    item.is_needed = False
    item.note = None
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    logger.info('shopping_item_purchased', name=purchase.item_name)
    return purchase


# --- Purchases --------------------------------------------------------------


@router.get('/purchases/', response_model=list[schemas.ShoppingPurchase], status_code=status.HTTP_200_OK)
def read_purchases(
    session: DbSession,
    zone: RequestZone,
    limit: CappedRowLimit = PURCHASES_SHOWN,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """The purchase log, most recent first. A bare day is read in the caller's zone."""
    purchases = models.ShoppingPurchase
    query = select(purchases).order_by(purchases.purchased_ts.desc(), purchases.id.desc())
    query = apply_date_bounds(query, purchases.purchased_ts, start_date, end_date, timezone=zone)
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.delete('/purchases/{id}/', status_code=status.HTTP_204_NO_CONTENT)
def undo_purchase(id: UUID, session: DbSession):
    """Undo a check-off: the record goes, and the item returns to the list with its note.

    An item already listed again since keeps the note it has now.
    """
    purchase = session.get(models.ShoppingPurchase, id)
    if purchase is None:
        raise NotFoundException('shopping purchase', id, logger)
    item = purchase.item
    if item is not None and not item.is_needed:
        item.is_needed = True
        item.note = purchase.note
    logger.info('shopping_purchase_undone', name=purchase.item_name)
    session.delete(purchase)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
