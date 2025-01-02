from pydantic import BaseModel
from pydantic import ConfigDict


class BoxItemConfig(BaseModel):
    """Base config class for BoxItem models."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BoxItemCreate(BoxItemConfig):
    """Pydantic model for creating a box item."""

    box_id: int
    name: str
    essential: bool
    warm: bool
    liquid: bool


class BoxItem(BoxItemConfig):
    """Pydantic model for a box item."""

    id: int
    box_id: int | None
    name: str
    essential: bool
    warm: bool
    liquid: bool

    @property
    def is_orphan(self) -> bool:
        """Return True if the item is not associated with a box."""
        return self.box_id is None


class BoxItemUpdate(BoxItemConfig):
    """Pydantic model for updating a box item."""

    id: int
    box_id: int | None = None
    name: str | None = None
    essential: bool | None = None
    warm: bool | None = None
    liquid: bool | None = None
