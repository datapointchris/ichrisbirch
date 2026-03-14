from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.boxitem import BoxItem


class BoxConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BoxCreate(BoxConfig):
    name: str
    number: int | None
    size: str
    essential: bool
    warm: bool
    liquid: bool


class Box(BoxConfig):
    id: int
    number: int | None
    name: str
    size: str
    essential: bool
    warm: bool
    liquid: bool
    items: list[BoxItem]

    @property
    def item_count(self):
        return len(self.items)


class BoxUpdate(BoxConfig):
    name: str | None = None
    number: int | None = None
    size: str | None = None
    essential: bool | None = None
    warm: bool | None = None
    liquid: bool | None = None
