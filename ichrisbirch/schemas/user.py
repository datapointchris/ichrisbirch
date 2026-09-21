from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

from ichrisbirch.schemas.not_null import NotNull


class UserConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserConfig):
    name: str
    email: str
    password: str

    @field_validator('name', 'email', 'password')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v


class User(UserConfig):
    id: int
    alternative_id: int
    name: str
    email: str
    password: str
    is_admin: bool
    created_on: datetime
    last_login: datetime | None
    preferences: Any


class UserUpdate(UserConfig):
    name: NotNull[str] = None
    email: NotNull[str] = None
    password: NotNull[str] = None
    is_admin: NotNull[bool] = None
    last_login: NotNull[datetime] = None
    preferences: NotNull[Any] = None
