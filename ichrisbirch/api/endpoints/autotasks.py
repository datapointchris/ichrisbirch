from fastapi_crudrouter import SQLAlchemyCRUDRouter

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
