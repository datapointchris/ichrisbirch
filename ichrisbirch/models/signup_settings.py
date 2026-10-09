from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class SignupSettings(Base):
    """The one row deciding whether `POST /users/` creates an account, read on every request."""

    __tablename__ = 'signup_settings'
    __table_args__ = (CheckConstraint('id = 1', name='single_row'), {'schema': 'admin'})

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return f'SignupSettings(is_open={self.is_open})'
