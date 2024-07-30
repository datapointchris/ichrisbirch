from datetime import datetime
from typing import Any
from typing import Optional

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
