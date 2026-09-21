from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.boxitem import BoxItem
from ichrisbirch.schemas.not_null import NotNull


class BoxConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BoxCreate(BoxConfig):
    name: str
    number: int
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
    name: NotNull[str] = None
    number: NotNull[int] = None
    size: NotNull[str] = None
    essential: NotNull[bool] = None
    warm: NotNull[bool] = None
    liquid: NotNull[bool] = None
