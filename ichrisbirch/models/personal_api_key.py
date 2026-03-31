import hashlib
import secrets
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base

KEY_PREFIX = 'icb_'
KEY_RANDOM_BYTES = 16  # 32 hex chars


def generate_api_key() -> str:
    """Generate a new personal API key: icb_ + 32 hex chars."""
    return KEY_PREFIX + secrets.token_hex(KEY_RANDOM_BYTES)


def hash_api_key(key: str) -> str:
    """SHA-256 hash of the full key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


class PersonalAPIKey(Base):
    __tablename__ = 'personal_api_keys'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    key_prefix: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f'PersonalAPIKey(name={self.name}, key_prefix={self.key_prefix}, user_id={self.user_id})'
