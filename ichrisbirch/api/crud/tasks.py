import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ichrisbirch.api.crud.base import CRUDBase
from ichrisbirch.models.tasks import Task
from ichrisbirch.schemas.tasks import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def read_many(self, db: Session, *, skip: int = 0, limit: int = 5000):
        return (
            db.query(Task)
            .filter(Task.complete_date.is_(None))
            .order_by(Task.priority.asc(), Task.add_date.asc())
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
    ):
        if first:
            return db.query(Task).filter(Task.complete_date.is_not(None)).order_by(Task.complete_date.asc()).first()

        elif last:
            return db.query(Task).filter(Task.complete_date.is_not(None)).order_by(Task.complete_date.desc()).first()

        elif start_date is None or end_date is None:
            return db.query(Task).filter(Task.complete_date.is_not(None)).order_by(Task.complete_date.desc()).all()

        else:
            return (
                db.query(Task)
                .filter(
                    Task.complete_date >= start_date,
                    Task.complete_date < end_date,
                )
                .order_by(Task.complete_date.desc())
                .all()
            )

    def complete_task(self, db: Session, id: int):
        if task := db.query(Task).filter(Task.id == id).first():
            task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        else:
            return None


tasks = CRUDTask(Task)
