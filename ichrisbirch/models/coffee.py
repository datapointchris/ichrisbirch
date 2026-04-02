from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

ROAST_LEVEL_VALUES = ['light', 'medium-light', 'medium', 'medium-dark', 'dark']
BREW_METHOD_VALUES = ['pour-over', 'espresso', 'french-press', 'aeropress', 'cold-brew', 'drip', 'moka-pot']


class RoastLevel(Base):
    """Lookup table for coffee roast levels."""

    __tablename__ = 'roast_levels'
    __table_args__ = {'schema': 'coffee'}
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class BrewMethod(Base):
    """Lookup table for coffee brew methods."""

    __tablename__ = 'brew_methods'
    __table_args__ = {'schema': 'coffee'}
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class CoffeeShop(Base):
    __tablename__ = 'coffee_shops'
    __table_args__ = {'schema': 'coffee'}
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_visited: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    beans: Mapped[list['CoffeeBean']] = relationship('CoffeeBean', back_populates='coffee_shop')

    def __repr__(self) -> str:
        return f'CoffeeShop(id={self.id!r}, name={self.name!r}, city={self.city!r})'


class CoffeeBean(Base):
    __tablename__ = 'coffee_beans'
    __table_args__ = {'schema': 'coffee'}
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    roaster: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[str | None] = mapped_column(Text, nullable=True)
    # process is free text — new methods emerge frequently, not worth a FK
    process: Mapped[str | None] = mapped_column(Text, nullable=True)
    roast_level: Mapped[str | None] = mapped_column(Text, ForeignKey('coffee.roast_levels.name'), nullable=True)
    brew_method: Mapped[str | None] = mapped_column(Text, ForeignKey('coffee.brew_methods.name'), nullable=True)
    flavor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Either a known shop or a free-text source (e.g. "Trade Coffee subscription") — mutually exclusive
    coffee_shop_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('coffee.coffee_shops.id', ondelete='SET NULL'), nullable=True)
    purchase_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    coffee_shop: Mapped['CoffeeShop | None'] = relationship('CoffeeShop', back_populates='beans')

    def __repr__(self) -> str:
        return f'CoffeeBean(id={self.id!r}, name={self.name!r}, roaster={self.roaster!r})'
