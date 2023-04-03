import logging
from datetime import datetime
from typing import Optional, TypeVar
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ichrisbirch import models, schemas

logger = logging.getLogger(__name__)

TaskModel = TypeVar('TaskModel', bound=models.Task)


class CRUDTask:
    """Class for Task CRUD operations"""

    # def __init__(self, model: models.Task):
    #     self.model = model

    def read_one(self, id: int, db: Session) -> Optional[models.Task]:
        """Default method for reading one row from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            id (Any): id of row to read

        Returns:
            Optional[ModelType]: row of db as a SQLAlchemy model
        """
        return db.query(models.Task).filter(models.Task.id == id).first()

    def read_many(self, db: Session, *, skip: int = 0, limit: int = 5000) -> list[models.Task]:
        """Read multiple rows of db

        Args:
            db (Session): SQLAlchemy Session to use for transaction
            skip (int, optional): Number of rows to skip. Defaults to 0.
            limit (int, optional): Limit for number of rows returned. Defaults to 5000.

        Returns:
            list[Task]: List of Task objects
        """
        return (
            db.query(models.Task)
            .filter(models.Task.complete_date.is_(None))
            .order_by(models.Task.priority.asc(), models.Task.add_date.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, task: schemas.TaskCreate, db: Session) -> models.Task:
        """Insert row in db from SQLAlchemy model

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            task (Pydantic schema): Schema for creating a db row

        Returns:
            ModelType: SQLAlchemy model of the inserted row
        """
        # task_data = jsonable_encoder(task)
        db_task = models.Task(**task.dict())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
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

    def delete(self, id: int, db: Session) -> models.Task | None:
        """Delete row from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            id (int): id of row to delete

        Returns:
            ModelType: SQLAlchemy model of the deleted row
            None: If the row does not exsit
        """
        if task := db.query(models.Task).filter(models.Task.id == id).first():
            db.delete(task)
            db.commit()
            return task
        return None

    def completed(
        self,
        db: Session,
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
        query = db.query(models.Task)
        completed = query.filter(models.Task.complete_date.is_not(None))

        if first:  # first completed task
            return completed.order_by(models.Task.complete_date.asc()).limit(1).all()

        if last:  # most recent (last) completed task
            return completed.order_by(models.Task.complete_date.desc()).limit(1).all()

        if start_date is None or end_date is None:  # return all if no start or end date
            return completed.order_by(models.Task.complete_date.desc()).all()

        return (  # filtered by start and end date
            query.filter(models.Task.complete_date >= start_date, models.Task.complete_date <= end_date)
            .order_by(models.Task.complete_date.desc())
            .all()
        )

    def complete_task(self, db: Session, id: Optional[int]) -> models.Task | None:
        """Complete task with specified id

        Args:
            db (Session): SQLAlchemy Session
            id (int): id of Task to mark completed

        Returns:
            Task | None: SQLAlchemy Task model or None if task is not found
        """
        if task := db.query(models.Task).filter(models.Task.id == id).first():
            task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()  # type: ignore
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        return None


tasks = CRUDTask()
