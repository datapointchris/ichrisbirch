from pydantic import BaseModel
from pydantic import ConfigDict


class BoxItemConfig(BaseModel):
    """Base config class for BoxItem models"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BoxItemCreate(BoxItemConfig):
    """Pydantic model for creating a box item"""

    box_id: int
    name: str
    essential: bool
    warm: bool
    liquid: bool


class BoxItem(BoxItemConfig):
    """Pydantic model for a box item"""

    id: int
    box_id: int
    name: str
    essential: bool
    warm: bool
    liquid: bool


class BoxItemUpdate(BoxItemConfig):
    """Pydantic model for updating a box item"""

    id: int
    box_id: int | None = None
    name: str | None = None
    essential: bool | None = None
    warm: bool | None = None
    liquid: bool | None = None
