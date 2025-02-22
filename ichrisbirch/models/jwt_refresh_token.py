from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.sqlalchemy.base import Base


class JWTRefreshToken(Base):
    __tablename__ = 'jwt_refresh_tokens'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    date_stored: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f'''
                JWTRefreshToken(user_id={self.user_id},
                refresh_token={self.refresh_token},
                date_stored={self.date_stored}
                '''
