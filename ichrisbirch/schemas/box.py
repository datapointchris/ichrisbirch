from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.models.box import BoxSize
from ichrisbirch.schemas.boxitem import BoxItem


class BoxConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BoxCreate(BoxConfig):
    """Pydantic model for creating a box."""

    name: str
    size: BoxSize
    essential: bool
    warm: bool
    liquid: bool


class Box(BoxConfig):
    """Pydantic model for a box."""

    id: int
    name: str
    size: BoxSize
    essential: bool
    warm: bool
    liquid: bool
    items: list[BoxItem]

    @property
    def item_count(self):
        return len(self.items)


class BoxUpdate(BoxConfig):
    """Pydantic model for updating a box."""

    id: int
    name: str | None = None
    size: BoxSize | None = None
    essential: bool | None = None
    warm: bool | None = None
    liquid: bool | None = None
