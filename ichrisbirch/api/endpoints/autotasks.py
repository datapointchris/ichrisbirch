import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models, schemas
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

settings = get_settings()
router = APIRouter(prefix='/autotasks', tags=['autotasks'], responses=settings.fastapi.responses)
logger = logging.getLogger(__name__)


@router.get('/', response_model=list[schemas.AutoTask], status_code=status.HTTP_200_OK)
async def read_many(session: Session = Depends(sqlalchemy_session)):
    """API method to read many autotasks."""
    query = select(models.AutoTask).order_by(models.AutoTask.last_run_date.desc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.AutoTask, status_code=status.HTTP_201_CREATED)
async def create(task: schemas.AutoTaskCreate, session: Session = Depends(sqlalchemy_session)):
    """API method to create a new task.  Passes request to crud.tasks module"""
    db_obj = models.AutoTask(**task.dict())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.AutoTask, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to read one task.  Passes request to crud.tasks module"""
    if autotask := session.get(models.AutoTask, id):
        return autotask
    else:
        message = f'AutoTask {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to delete a task.  Passes request to crud.tasks module"""
    if autotask := session.get(models.AutoTask, id):
        session.delete(autotask)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        message = f'AutoTask {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/{id}/run/', status_code=status.HTTP_200_OK)
async def run(id: int, session: Session = Depends(sqlalchemy_session)):
    """API method to run a task.  Passes request to crud.tasks module"""
    if autotask := session.get(models.AutoTask, id):
        task = models.Task(
            name=autotask.name, notes=autotask.notes, priority=autotask.priority, category=autotask.category
        )
        session.add(task)
        autotask.last_run_date = datetime.now()
        autotask.run_count += 1
        session.commit()
        session.refresh(task)
        logger.debug(f'Ran autotask {id}, created task {task.id}')
        return task
    else:
        message = f'AutoTask {id} not found'
        logger.warning(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
