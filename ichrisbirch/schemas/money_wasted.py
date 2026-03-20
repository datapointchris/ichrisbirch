from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


class MoneyWastedConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MoneyWastedCreate(MoneyWastedConfig):
    item: str
    amount: float
    date_purchased: date | None = None
    date_wasted: date
    notes: str | None = None

    @field_validator('date_purchased', mode='before')
    @classmethod
    def set_date_purchased(cls, v):
        if v == '':
            return None
        return v


class MoneyWasted(MoneyWastedConfig):
    id: int
    item: str
    amount: float
    date_purchased: date | None
    date_wasted: date
    notes: str | None


class MoneyWastedUpdate(MoneyWastedConfig):
    item: str | None = None
    amount: float | None = None
    date_purchased: date | None = None
    date_wasted: date | None = None
    notes: str | None = None

    @field_validator('date_purchased')
    @classmethod
    def set_date_purchased(cls, v):
        if v == '':
            return None
        return v
