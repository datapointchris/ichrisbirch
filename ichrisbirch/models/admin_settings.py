from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class AdminSettings(Base):
    """The one row of settings an admin changes without a redeploy. Each is read on every request it governs."""

    __tablename__ = 'settings'
    __table_args__ = (CheckConstraint('id = 1', name='single_row'), {'schema': 'admin'})

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_signup_open: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return f'AdminSettings(is_signup_open={self.is_signup_open})'
