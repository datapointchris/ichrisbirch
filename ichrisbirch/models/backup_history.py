from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy_json import mutable_json_type

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.backup_restore import BackupRestore
    from ichrisbirch.models.user import User

MutableJSONB = mutable_json_type(dbtype=JSONB, nested=True)


class BackupHistory(Base):
    """Model for tracking database backup history.

    Stores metadata about each backup including table snapshots,
    duration, file size, checksums, and which user triggered it.
    """

    __tablename__ = 'backup_history'
    __table_args__ = {'schema': 'admin'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    backup_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'scheduled' | 'manual'
    environment: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    table_snapshot: Mapped[dict | None] = mapped_column(MutableJSONB, nullable=True)
    postgres_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    database_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)

    triggered_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    triggered_by_user: Mapped['User | None'] = relationship('User', foreign_keys=[triggered_by_user_id])

    restores: Mapped[list['BackupRestore']] = relationship(
        'BackupRestore',
        back_populates='backup',
        order_by='BackupRestore.restored_at',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'BackupHistory(filename={self.filename!r}, success={self.success}, created_at={self.created_at})'
