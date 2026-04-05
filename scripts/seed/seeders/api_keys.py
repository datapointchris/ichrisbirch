"""Seed a well-known dev API key so external tools (todoui) can connect."""

from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.personal_api_key import PersonalAPIKey
from ichrisbirch.models.personal_api_key import hash_api_key
from ichrisbirch.models.user import User
from scripts.seed.base import SeedResult

DEV_API_KEY = 'icb_dev00000000000000000000000000'
DEV_API_KEY_HASH = hash_api_key(DEV_API_KEY)


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text("DELETE FROM personal_api_keys WHERE name = 'todoui-dev'"))


def seed(session: Session, scale: int = 1) -> SeedResult:
    existing = session.query(PersonalAPIKey).filter(PersonalAPIKey.hashed_key == DEV_API_KEY_HASH).first()
    if existing:
        return SeedResult(model='PersonalAPIKey', count=0, details='already exists')

    user = session.query(User).first()
    if not user:
        return SeedResult(model='PersonalAPIKey', count=0, details='no user found')

    session.add(
        PersonalAPIKey(
            user_id=user.id,
            name='todoui-dev',
            key_prefix=DEV_API_KEY[:8],
            hashed_key=DEV_API_KEY_HASH,
        )
    )
    session.flush()
    return SeedResult(model='PersonalAPIKey', count=1, details='dev key for todoui')
