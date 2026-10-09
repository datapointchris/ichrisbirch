from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class SignupSettingsConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SignupSettings(SignupSettingsConfig):
    is_open: bool


class SignupSettingsUpdate(SignupSettingsConfig):
    is_open: NotNull[bool] = None
