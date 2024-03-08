import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# from ..dependencies import auth
from ichrisbirch import models, schemas
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/boxes/', response_model=list[schemas.Box], status_code=status.HTTP_200_OK)
async def read_many_boxes(session: Session = Depends(sqlalchemy_session), limit: Optional[int] = None):
    query = select(models.Box).order_by(models.Box.id)
    query = query.limit(limit) if limit else query
    results = list(session.scalars(query).all())
    logger.debug(f'getting {len(results)} boxes')
    return results


@router.post('/boxes/', response_model=schemas.Box, status_code=status.HTTP_201_CREATED)
async def create_box(box: schemas.BoxCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.Box(**box.model_dump())
    logger.debug(f'creating {db_obj=}')
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.debug(f'created {db_obj=}')
    return db_obj


@router.get('/boxes/{id}/', response_model=schemas.Box, status_code=status.HTTP_200_OK)
async def read_one_box(id: int, session: Session = Depends(sqlalchemy_session)):
    if box := session.get(models.Box, id):
        logger.debug(f'getting {box=}')
        return box
    else:
        message = f'Box {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/boxes/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_box(id: int, session: Session = Depends(sqlalchemy_session)):
    if box := session.get(models.Box, id):
        logger.debug(f'deleting {box=}')
        session.delete(box)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'Box {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/items/', response_model=list[schemas.BoxItem], status_code=status.HTTP_200_OK)
async def read_many_items(session: Session = Depends(sqlalchemy_session), limit: Optional[int] = None):
    logger.debug(f'getting {limit=} box items')
    query = select(models.BoxItem).order_by(models.BoxItem.id)
    query = query.limit(limit) if limit else query
    return list(session.scalars(query).all())


@router.post('/items/', response_model=schemas.BoxItem, status_code=status.HTTP_201_CREATED)
async def create_item(item: schemas.BoxItemCreate, session: Session = Depends(sqlalchemy_session)):
    db_obj = models.BoxItem(**item.model_dump())
    logger.debug(f'creating {db_obj=}')
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.debug(f'created {db_obj=}')
    return db_obj


@router.get('/items/{id}/', response_model=schemas.BoxItem, status_code=status.HTTP_200_OK)
async def read_one_item(id: int, session: Session = Depends(sqlalchemy_session)):
    if item := session.get(models.BoxItem, id):
        logger.debug(f'getting {item=}')
        return item
    else:
        message = f'BoxItem {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/items/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(id: int, session: Session = Depends(sqlalchemy_session)):
    if item := session.get(models.BoxItem, id):
        logger.debug(f'deleting {item=}')
        session.delete(item)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'BoxItem {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/search/', response_model=list[schemas.BoxItem], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(sqlalchemy_session)):
    """API method to search for boxes or items"""
    logger.debug(f'searching for {q=}')
    items = select(models.BoxItem).filter(models.BoxItem.name.ilike('%' + q + '%'))
    results = session.scalars(items).all()
    logger.debug(f'search found {len(results)} results')
    return results
