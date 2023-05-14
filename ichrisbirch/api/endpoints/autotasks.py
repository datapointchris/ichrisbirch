from fastapi import Depends
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models, schemas
from ichrisbirch.config import get_settings
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

settings = get_settings()

router = SQLAlchemyCRUDRouter(
    prefix='/autotasks',
    tags=['autotasks'],
    db_model=models.AutoTask,
    db=sqlalchemy_session,
    schema=schemas.AutoTask,
    create_schema=schemas.AutoTaskCreate,
    update_route=False,
    delete_all_route=False,
    responses=settings.fastapi.responses,
)


@router.get("/", response_model=list[schemas.AutoTask])
async def read_many(session: Session = Depends(sqlalchemy_session)):
    """API method to read many autotasks."""

    query = select(models.AutoTask).order_by(models.AutoTask.last_run_date.desc())
    return list(session.scalars(query).all())
