from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator


class CoffeeShopConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CoffeeShopCreate(CoffeeShopConfig):
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    google_maps_url: str | None = None
    website: str | None = None
    rating: float | None = None
    notes: str | None = None
    review: str | None = None
    date_visited: datetime | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class CoffeeShop(CoffeeShopConfig):
    id: int
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    google_maps_url: str | None = None
    website: str | None = None
    rating: float | None = None
    notes: str | None = None
    review: str | None = None
    date_visited: datetime | None = None
    created_at: datetime


class CoffeeShopUpdate(CoffeeShopConfig):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    google_maps_url: str | None = None
    website: str | None = None
    rating: float | None = None
    notes: str | None = None
    review: str | None = None
    date_visited: datetime | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class CoffeeBeanConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CoffeeBeanCreate(CoffeeBeanConfig):
    name: str
    roaster: str | None = None
    origin: str | None = None
    process: str | None = None
    roast_level: str | None = None
    brew_method: str | None = None
    flavor_notes: str | None = None
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    price: float | None = None
    purchase_date: datetime | None = None
    coffee_shop_id: int | None = None
    purchase_source: str | None = None
    purchase_url: str | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class CoffeeBean(CoffeeBeanConfig):
    id: int
    name: str
    roaster: str | None = None
    origin: str | None = None
    process: str | None = None
    roast_level: str | None = None
    brew_method: str | None = None
    flavor_notes: str | None = None
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    price: float | None = None
    purchase_date: datetime | None = None
    coffee_shop_id: int | None = None
    purchase_source: str | None = None
    purchase_url: str | None = None
    created_at: datetime


class CoffeeBeanUpdate(CoffeeBeanConfig):
    name: str | None = None
    roaster: str | None = None
    origin: str | None = None
    process: str | None = None
    roast_level: str | None = None
    brew_method: str | None = None
    flavor_notes: str | None = None
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    price: float | None = None
    purchase_date: datetime | None = None
    coffee_shop_id: int | None = None
    purchase_source: str | None = None
    purchase_url: str | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data
