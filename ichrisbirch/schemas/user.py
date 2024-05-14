from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict


class UserConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserConfig):
    name: str
    email: str
    password: str


class User(UserConfig):
    id: int
    alternative_id: int
    name: str
    email: str
    created_on: datetime
    last_login: datetime | None
    preferences: Any


class UserUpdate(UserConfig):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    preferences: Any | None = None
