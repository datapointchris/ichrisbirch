import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models, schemas

logger = logging.getLogger(__name__)


class CRUDTask:
    """Class for Task CRUD operations"""

    # def __init__(self, model: models.Task):
    #     self.model = model

    def read_one(self, id: int, session: Session) -> Optional[models.Task]:
        """Default method for reading one row from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            id (Any): id of row to read

        Returns:
            Optional[ModelType]: row of db as a SQLAlchemy model
        """
        if task := session.get(models.Task, id):
            return task
        logger.warning(f'Task {id} not found')
        return None

    def read_many(
        self, session: Session, completed_filter: Optional[str] = None, limit: Optional[int] = None
    ) -> list[models.Task]:
        """Read multiple rows of db

        Args:
            db (Session): SQLAlchemy Session to use for transaction
            limit (int, optional): Limit for number of rows returned. Defaults to 5000.

        Returns:
            list[Task]: List of Task objects
        """
        print(f'{completed_filter=}')
        query = select(models.Task)

        if completed_filter == 'completed':
            query = query.filter(models.Task.complete_date.is_not(None))

        if completed_filter == 'not_completed':
            query = query.filter(models.Task.complete_date.is_(None))

        query = query.order_by(models.Task.priority.asc(), models.Task.add_date.asc())
        if limit:
            query = query.limit(limit)
        return list(session.scalars(query).all())

    def create(self, task: schemas.TaskCreate, session: Session) -> models.Task:
        """Insert row in db from SQLAlchemy model

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            task (Pydantic schema): Schema for creating a db row

        Returns:
            ModelType: SQLAlchemy model of the inserted row
        """
        db_task = models.Task(**task.dict())
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task

    # TODO: https://github.com/tiangolo/full-stack-fastapi-postgresql
    # def update(self, task: Union[schemas.TaskUpdate, dict[str, Any]], db: Session) -> models.Task:
    #     """Update db row

    #     Args:
    #         db (SQLAlchemy Session): Session to use for transaction
    #         task (Union[UpdateSchemaType, Dict[str, Any]]): Pydantic model or dict to insert

    #     Returns:
    #         ModelType: SQLAlchemy model of the updated row
    #     """
    #     task_data = jsonable_encoder(task)
    #     if isinstance(task, dict):
    #         update_data = task
    #     else:
    #         update_data = task.dict(exclude_unset=True)
    #     for field in task_data:
    #         if field in update_data:
    #             setattr(db_obj, field, update_data[field])
    #     db.add(db_obj)
    #     db.commit()
    #     db.refresh(db_obj)
    #     return db_obj

    def delete(self, id: int, session: Session) -> models.Task | None:
        """Delete row from db

        Args:
            session (SQLAlchemy Session): Session to use for transaction
            id (int): id of row to delete

        Returns:
            Union[ModelType, None]: SQLAlchemy model of the deleted row or None if the row does not exist
        """
        if task := session.get(models.Task, id):
            session.delete(task)
            session.commit()
            return task
        logger.warn(f'Task {id} not found')
        return None

    def completed(
        self,
        session: Session,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        first: bool | None = None,
        last: bool | None = None,
    ) -> list[models.Task]:
        """Return completed tasks for specified time period

        Args:
            db (Session): SQLAlchemy Session
            start_date (str | None, optional): Start date of time period. Defaults to None.
            end_date (str | None, optional): End date of time period. Defaults to None.
            first (bool | None, optional): Return first completed task. Defaults to None.
            last (bool | None, optional): Return last completed task. Defaults to None.

        Returns:
            list[Task] | Task: SQLAlchemy Task model(s)
        """
        statement = select(models.Task).filter(models.Task.complete_date.is_not(None))

        if first:  # first completed task
            statement = statement.order_by(models.Task.complete_date.asc()).limit(1)

        elif last:  # most recent (last) completed task
            statement = statement.order_by(models.Task.complete_date.desc()).limit(1)

        elif start_date is None or end_date is None:  # return all if no start or end date
            statement = statement.order_by(models.Task.complete_date.desc())

        else:  # filtered by start and end date
            statement = statement.filter(
                models.Task.complete_date >= start_date, models.Task.complete_date <= end_date
            ).order_by(models.Task.complete_date.desc())

        return list(session.scalars(statement).all())

    def complete_task(self, id: int, session: Session) -> models.Task | None:
        """Complete task with specified id

        Args:
            db (Session): SQLAlchemy Session
            id (int): id of Task to mark completed

        Returns:
            Task | None: SQLAlchemy Task model or None if task is not found
        """
        if task := session.get(models.Task, id):
            task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()  # type: ignore
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        logger.warn(f'Task {id} not found')
        return None


tasks = CRUDTask()
