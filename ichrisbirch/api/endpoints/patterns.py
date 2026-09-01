import structlog
from fastapi import APIRouter
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.services.row_limit import RowLimit
from ichrisbirch.services.row_limit import apply_row_limit

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.Pattern], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession, search: str | None = None, limit: RowLimit = None):
    query = select(models.Pattern).order_by(models.Pattern.recorded_at.desc())
    if search:
        query = query.where(models.Pattern.message.ilike(f'%{search}%'))
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.post('/', response_model=schemas.Pattern, status_code=status.HTTP_201_CREATED)
async def create(pattern: schemas.PatternCreate, session: DbSession):
    db_obj = models.Pattern(**pattern.model_dump(exclude_none=True))
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.Pattern, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if pattern := session.get(models.Pattern, id):
        return pattern
    raise NotFoundException('pattern', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if pattern := session.get(models.Pattern, id):
        session.delete(pattern)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('pattern', id, logger)


@router.patch('/{id}/', response_model=schemas.Pattern, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.PatternUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('pattern_update', pattern_id=id, update_data=update_data)

    if pattern := session.get(models.Pattern, id):
        for attr, value in update_data.items():
            setattr(pattern, attr, value)
        session.commit()
        session.refresh(pattern)
        return pattern

    raise NotFoundException('pattern', id, logger)
