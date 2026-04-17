from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

RECIPE_UNITS = [
    'cup',
    'tbsp',
    'tsp',
    'oz',
    'fl_oz',
    'lb',
    'g',
    'kg',
    'ml',
    'l',
    'pinch',
    'dash',
    'clove',
    'slice',
    'can',
    'package',
    'piece',
    'scoop',
    'whole',
    'to_taste',
]

RECIPE_DIFFICULTIES = ['easy', 'medium', 'hard']

RECIPE_CUISINES = [
    'american',
    'italian',
    'mexican',
    'asian',
    'indian',
    'mediterranean',
    'french',
    'other',
]

RECIPE_MEAL_TYPES = [
    'breakfast',
    'lunch',
    'dinner',
    'snack',
    'dessert',
    'side',
    'sauce',
    'drink',
]


class RecipeUnit(Base):
    """Lookup table for ingredient units."""

    __tablename__ = 'recipe_units'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class RecipeDifficulty(Base):
    """Lookup table for recipe difficulty."""

    __tablename__ = 'recipe_difficulty'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class RecipeCuisine(Base):
    """Lookup table for recipe cuisine."""

    __tablename__ = 'recipe_cuisine'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class RecipeMealType(Base):
    """Lookup table for recipe meal type."""

    __tablename__ = 'recipe_meal_type'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Recipe(Base):
    __tablename__ = 'recipes'

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    source_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int] = mapped_column(Integer, nullable=False, server_default='4')
    difficulty: Mapped[str | None] = mapped_column(Text, ForeignKey('recipe_difficulty.name'), nullable=True)
    cuisine: Mapped[str | None] = mapped_column(Text, ForeignKey('recipe_cuisine.name'), nullable=True)
    meal_type: Mapped[str | None] = mapped_column(Text, ForeignKey('recipe_meal_type.name'), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(postgresql.ARRAY(Text), nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    times_made: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    last_made_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    ingredients: Mapped[list['RecipeIngredient']] = relationship(
        'RecipeIngredient',
        back_populates='recipe',
        cascade='all, delete-orphan',
        order_by='RecipeIngredient.position',
    )

    def __repr__(self) -> str:
        return f'Recipe(id={self.id!r}, name={self.name!r}, cuisine={self.cuisine!r}, servings={self.servings!r})'


class RecipeIngredient(Base):
    __tablename__ = 'recipe_ingredients'

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(Text, ForeignKey('recipe_units.name'), nullable=True)
    item: Mapped[str] = mapped_column(Text, nullable=False)
    prep_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')
    ingredient_group: Mapped[str | None] = mapped_column(Text, nullable=True)

    recipe: Mapped['Recipe'] = relationship('Recipe', back_populates='ingredients')

    def __repr__(self) -> str:
        return f'RecipeIngredient(id={self.id!r}, recipe_id={self.recipe_id!r}, item={self.item!r})'
