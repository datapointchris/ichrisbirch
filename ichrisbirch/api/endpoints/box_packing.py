import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.database.session import get_sqlalchemy_session

logger = structlog.get_logger()
router = APIRouter()


@router.get('/search/', response_model=list[tuple[schemas.Box, schemas.BoxItem]], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(get_sqlalchemy_session)):
    """This search is different from the other searches as it joins the Box and BoxItem tables and returns a list of tuples of Box and
    BoxItem objects instead of only BoxItem objects.

    This requires the QueryAPI to use the `get_generic` method instead of the `get_many` method since this search
    returns more than one type of ModelType.
    """
    logger.debug('box_search', query=q)
    items = select(models.Box, models.BoxItem).join(models.Box).filter(models.BoxItem.name.ilike('%' + q + '%'))
    results = session.execute(items).all()
    logger.debug('box_search_results', count=len(results))
    return list(results)


@router.get('/boxes/', response_model=list[schemas.Box], status_code=status.HTTP_200_OK)
async def read_many_boxes(session: Session = Depends(get_sqlalchemy_session), limit: int | None = None):
    query = select(models.Box).order_by(models.Box.number)
    query = query.limit(limit) if limit else query
    results = list(session.scalars(query).all())
    return results


@router.post('/boxes/', response_model=schemas.Box, status_code=status.HTTP_201_CREATED)
async def create_box(box: schemas.BoxCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.Box(**box.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/boxes/{id}/', response_model=schemas.Box, status_code=status.HTTP_200_OK)
async def read_one_box(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if box := session.get(models.Box, id):
        return box
    raise NotFoundException('box', id, logger)


@router.delete('/boxes/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_box(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if box := session.get(models.Box, id):
        # orphan items in box
        for item in box.items:
            item.box_id = None
            logger.debug('box_item_orphaned', item_name=item.name, box_id=id, box_name=box.name)
        session.delete(box)
        session.commit()
        return {'message': 'Item deleted'}
    raise NotFoundException('box', id, logger)


@router.patch('/boxes/{id}/', response_model=schemas.Box, status_code=status.HTTP_200_OK)
async def update_box(id: int, update: schemas.BoxUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('box_update', box_id=id, update_data=update_data)
    if obj := session.get(models.Box, id):
        for attr, value in update_data.items():
            setattr(obj, attr, value)
        session.commit()
        session.refresh(obj)
        return obj
    raise NotFoundException('box', id, logger)


@router.get('/items/', response_model=list[schemas.BoxItem], status_code=status.HTTP_200_OK)
async def read_many_items(session: Session = Depends(get_sqlalchemy_session), limit: int | None = None):
    query = select(models.BoxItem).order_by(models.BoxItem.name)
    query = query.limit(limit) if limit else query
    return list(session.scalars(query).all())


def _update_box_details_based_on_contents(box: models.Box, session: Session):
    """Update the box details based on the items in the box.

    When a new item is added or deleted from the box, see if it changes the box details
    """
    for attr in ('liquid', 'warm', 'essential'):
        value = any(getattr(item, attr) for item in box.items)
        if value != getattr(box, attr):
            setattr(box, attr, value)
            logger.debug('box_attr_changed', box_id=box.id, attr=attr, new_value=getattr(box, attr))
    session.commit()


@router.post('/items/', response_model=schemas.BoxItem, status_code=status.HTTP_201_CREATED)
async def create_item(item: schemas.BoxItemCreate, session: Session = Depends(get_sqlalchemy_session)):
    db_obj = models.BoxItem(**item.model_dump())
    session.add(db_obj)
    session.commit()
    _update_box_details_based_on_contents(db_obj.box, session)
    session.refresh(db_obj)
    return db_obj


@router.get('/items/orphans/', response_model=list[schemas.BoxItem], status_code=status.HTTP_200_OK)
async def read_many_orphans(session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.BoxItem).filter(models.BoxItem.box_id.is_(None)).order_by(models.BoxItem.name)
    return list(session.scalars(query).all())


@router.get('/items/{id}/', response_model=schemas.BoxItem, status_code=status.HTTP_200_OK)
async def read_one_item(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if item := session.get(models.BoxItem, id):
        return item
    raise NotFoundException('box item', id, logger)


@router.delete('/items/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if item := session.get(models.BoxItem, id):
        box = item.box
        session.delete(item)
        session.commit()
        if box:  # if item was in a box and not an orphan
            _update_box_details_based_on_contents(box, session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('box item', id, logger)


@router.patch('/items/{id}/', response_model=schemas.BoxItem, status_code=status.HTTP_200_OK)
async def update_item(id: int, update: schemas.BoxItemUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('box_item_update', item_id=id, update_data=update_data)
    if obj := session.get(models.BoxItem, id):
        for attr, value in update_data.items():
            setattr(obj, attr, value)
        session.commit()
        session.refresh(obj)
        return obj
    raise NotFoundException('box item', id, logger)
