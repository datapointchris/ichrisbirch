from fastapi_crudrouter import SQLAlchemyCRUDRouter

from ichrisbirch import models, schemas
from ichrisbirch.config import get_settings
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

settings = get_settings()

router = SQLAlchemyCRUDRouter(
    prefix='/countdowns',
    tags=['countdowns'],
    db_model=models.Countdown,
    db=sqlalchemy_session,
    schema=schemas.Countdown,
    create_schema=schemas.CountdownCreate,
    update_route=False,
    delete_all_route=False,
    responses=settings.fastapi.responses,
)
