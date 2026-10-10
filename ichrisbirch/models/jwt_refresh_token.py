import datetime as dt

from sqlalchemy import DateTime
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class JWTRefreshToken(Base):
    """A table nothing reads or writes, declared until the migration that drops it.

    The release before the drop still reads it, so the drop waits until that release is no longer
    the live color.
    """

    __tablename__ = 'jwt_refresh_tokens'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    date_stored: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
