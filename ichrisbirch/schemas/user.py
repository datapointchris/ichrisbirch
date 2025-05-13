from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


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
            raise ValueError("Field cannot be empty")
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
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    last_login: Optional[datetime] = None
    preferences: Optional[Any] = None
