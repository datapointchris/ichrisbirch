from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo

from .base import CRUDBase
from ...common.models.tasks import Task
from ...common.schemas.tasks import TaskCreate, TaskUpdate

import logging

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
        last: bool | None = None
    ):
        if first:
            result = (
                db.query(Task)
                .filter(Task.complete_date.is_not(None))
                .order_by(Task.complete_date.asc())
                .first()
            )
        elif last:
            result = (
                db.query(Task)
                .filter(Task.complete_date.is_not(None))
                .order_by(Task.complete_date.desc())
                .first()
            )
        elif start_date is None and end_date is None:
            result = (
                db.query(Task)
                .filter(Task.complete_date.is_not(None))
                .order_by(Task.complete_date.desc())
                .all()
            )
        else:
            result = (
                db.query(Task)
                .filter(
                    Task.complete_date >= start_date,
                    Task.complete_date < end_date,
                )
                .order_by(Task.complete_date.desc())
                .all()
            )
        return result

    def complete_task(self, db: Session, id: int):
        task = self.read_one(db, id)
        print(task)
        task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago")).isoformat()
        db.add(task)
        db.commit()
        db.refresh(task)
        return task


tasks = CRUDTask(Task)
