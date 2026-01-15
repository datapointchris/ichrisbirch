from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.backup_history import BackupHistory
    from ichrisbirch.models.user import User


class BackupRestore(Base):
    """Model for tracking database restore events.

    Each restore operation creates a record linked to the backup
    that was restored, tracking success/failure and duration.
    """

    __tablename__ = 'backup_restores'
    __table_args__ = {'schema': 'admin'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backup_id: Mapped[int] = mapped_column(Integer, ForeignKey('admin.backup_history.id'), nullable=False)
    backup: Mapped['BackupHistory'] = relationship('BackupHistory', back_populates='restores')

    restored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    restored_to_environment: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    restored_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    restored_by_user: Mapped['User | None'] = relationship('User', foreign_keys=[restored_by_user_id])

    def __repr__(self) -> str:
        return f'BackupRestore(backup_id={self.backup_id}, restored_at={self.restored_at}, success={self.success})'
