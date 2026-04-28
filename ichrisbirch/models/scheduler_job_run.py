from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class SchedulerJobRun(Base):
    """Tracks execution history for APScheduler jobs."""

    __tablename__ = 'scheduler_job_runs'
    __table_args__ = {'schema': 'admin'}

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    job_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    job_run_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f'SchedulerJobRun(job_id={self.job_id!r}, success={self.success}, started_at={self.started_at})'
