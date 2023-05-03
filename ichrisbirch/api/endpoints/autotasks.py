from fastapi_crudrouter import SQLAlchemyCRUDRouter

from ichrisbirch import models, schemas
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

router = SQLAlchemyCRUDRouter(
    schema=schemas.AutoTask,
    create_schema=schemas.AutoTaskCreate,
    update_route=False,
    delete_all_route=False,
    db_model=models.AutoTask,
    db=sqlalchemy_session,
    prefix='/autotasks',
    tags=['autotasks'],
)
