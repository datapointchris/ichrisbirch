from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class AdminSettingsConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AdminSettings(AdminSettingsConfig):
    is_signup_open: bool


class AdminSettingsUpdate(AdminSettingsConfig):
    is_signup_open: NotNull[bool] = None
