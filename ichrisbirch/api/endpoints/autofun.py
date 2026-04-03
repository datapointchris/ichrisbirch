import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession

logger = structlog.get_logger()
router = APIRouter()


@router.get('/', response_model=list[schemas.AutoFun], status_code=status.HTTP_200_OK)
async def read_many(session: DbSession, completed: bool | None = None):
    query = select(models.AutoFun).order_by(models.AutoFun.added_date.desc())
    if completed is not None:
        query = query.where(models.AutoFun.is_completed == completed)
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.AutoFun, status_code=status.HTTP_201_CREATED)
async def create(autofun: schemas.AutoFunCreate, session: DbSession):
    db_obj = models.AutoFun(**autofun.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get('/{id}/', response_model=schemas.AutoFun, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if autofun := session.get(models.AutoFun, id):
        return autofun
    logger.warning('autofun_not_found', id=id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'AutoFun {id} not found')


@router.patch('/{id}/', response_model=schemas.AutoFun, status_code=status.HTTP_200_OK)
async def update(id: int, autofun_update: schemas.AutoFunUpdate, session: DbSession):
    if db_obj := session.get(models.AutoFun, id):
        for field, value in autofun_update.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        session.commit()
        session.refresh(db_obj)
        return db_obj
    logger.warning('autofun_not_found', id=id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'AutoFun {id} not found')


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if autofun := session.get(models.AutoFun, id):
        # Remove any active task junction record before deleting the item
        active = session.execute(select(models.AutoFunActiveTask).where(models.AutoFunActiveTask.fun_item_id == id)).scalar_one_or_none()
        if active:
            session.delete(active)
        session.delete(autofun)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    logger.warning('autofun_not_found', id=id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'AutoFun {id} not found')
