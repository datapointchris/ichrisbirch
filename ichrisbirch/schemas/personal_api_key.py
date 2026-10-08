import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict


class PersonalAPIKeyConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PersonalAPIKeyCreate(PersonalAPIKeyConfig):
    name: str


class PersonalAPIKey(PersonalAPIKeyConfig):
    id: int
    name: str
    key_prefix: str
    created_at: dt.datetime
    last_used_at: dt.datetime | None = None
    revoked_at: dt.datetime | None = None


class PersonalAPIKeyCreated(PersonalAPIKey):
    """Returned only at creation time — includes the full key."""

    key: str
