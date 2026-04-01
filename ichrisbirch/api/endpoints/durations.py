import structlog
from fastapi import APIRouter
from fastapi import Response
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.Duration], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession):
    query = select(models.Duration).options(selectinload(models.Duration.duration_notes)).order_by(models.Duration.start_date.asc())
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Duration, status_code=status.HTTP_201_CREATED)
async def create(duration: schemas.DurationCreate, session: DbSession):
    db_obj = models.Duration(**duration.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.Duration, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    query = select(models.Duration).options(selectinload(models.Duration.duration_notes)).where(models.Duration.id == id)
    if duration := session.scalars(query).first():
        return duration
    raise NotFoundException('duration', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if duration := session.get(models.Duration, id):
        session.delete(duration)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('duration', id, logger)


@router.patch('/{id}/', response_model=schemas.Duration, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.DurationUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('duration_update', duration_id=id, update_data=update_data)

    if duration := session.get(models.Duration, id):
        for attr, value in update_data.items():
            setattr(duration, attr, value)
        session.commit()
        session.refresh(duration)
        return duration
    raise NotFoundException('duration', id, logger)


# --- Note endpoints ---


@router.post('/{id}/notes/', response_model=schemas.DurationNote, status_code=status.HTTP_201_CREATED)
async def create_note(id: int, note: schemas.DurationNoteCreate, session: DbSession):
    if not session.get(models.Duration, id):
        raise NotFoundException('duration', id, logger)
    db_obj = models.DurationNote(duration_id=id, **note.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.patch('/{id}/notes/{note_id}/', response_model=schemas.DurationNote, status_code=status.HTTP_200_OK)
async def update_note(id: int, note_id: int, update: schemas.DurationNoteUpdate, session: DbSession):
    if not session.get(models.Duration, id):
        raise NotFoundException('duration', id, logger)
    note_obj = session.get(models.DurationNote, note_id)
    if not note_obj or note_obj.duration_id != id:
        raise NotFoundException('duration_note', note_id, logger)

    update_data = update.model_dump(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(note_obj, attr, value)
    session.commit()
    session.refresh(note_obj)
    return note_obj


@router.delete('/{id}/notes/{note_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(id: int, note_id: int, session: DbSession):
    if not session.get(models.Duration, id):
        raise NotFoundException('duration', id, logger)
    note_obj = session.get(models.DurationNote, note_id)
    if not note_obj or note_obj.duration_id != id:
        raise NotFoundException('duration_note', note_id, logger)

    session.delete(note_obj)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
