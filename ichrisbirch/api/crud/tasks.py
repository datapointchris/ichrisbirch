import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ichrisbirch import models, schemas
from ichrisbirch.api.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDTask(CRUDBase[models.Task, schemas.TaskCreate, schemas.TaskUpdate]):
    """Class for Task CRUD operations"""

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

    def completed(
        self,
        db: Session,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        first: bool | None = None,
        last: bool | None = None,
    ) -> list[models.Task] | models.Task:
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
        if first:
            return (
                db.query(models.Task)
                .filter(models.Task.complete_date.is_not(None))
                .order_by(models.Task.complete_date.asc())
                .first()
            )

        elif last:
            return (
                db.query(models.Task)
                .filter(models.Task.complete_date.is_not(None))
                .order_by(models.Task.complete_date.desc())
                .first()
            )

        elif start_date is None or end_date is None:
            return (
                db.query(models.Task)
                .filter(models.Task.complete_date.is_not(None))
                .order_by(models.Task.complete_date.desc())
                .all()
            )

        else:
            return (
                db.query(models.Task)
                .filter(
                    models.Task.complete_date >= start_date,
                    models.Task.complete_date < end_date,
                )
                .order_by(models.Task.complete_date.desc())
                .all()
            )

    def complete_task(self, db: Session, id: int) -> models.Task | None:
        """Complete task with specified id

        Args:
            db (Session): SQLAlchemy Session
            id (int): id of Task to mark completed

        Returns:
            Task | None: SQLAlchemy Task model or None if task is not found
        """
        if task := db.query(models.Task).filter(models.Task.id == id).first():
            task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        else:
            return None


tasks = CRUDTask(models.Task)
