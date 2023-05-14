from fastapi_crudrouter import SQLAlchemyCRUDRouter

from ichrisbirch import models, schemas
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

router = SQLAlchemyCRUDRouter(
    schema=schemas.Countdown,
    create_schema=schemas.CountdownCreate,
    update_route=False,
    delete_all_route=False,
    db_model=models.Countdown,
    db=sqlalchemy_session
)
