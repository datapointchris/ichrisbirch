from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class RecipeConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientBase(RecipeConfig):
    position: int = 0
    quantity: float | None = None
    unit: str | None = None
    item: str
    prep_note: str | None = None
    is_optional: bool = False
    ingredient_group: str | None = None


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredient(RecipeIngredientBase):
    id: int
    recipe_id: int
    scaled_quantity: float | None = None


class RecipeBase(RecipeConfig):
    name: str
    description: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    total_time_minutes: int | None = None
    servings: int = 4
    difficulty: str | None = None
    cuisine: str | None = None
    meal_type: str | None = None
    tags: list[str] | None = None
    instructions: str
    notes: str | None = None
    rating: int | None = None


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (v if isinstance(v, list | dict | bool | int | float) else (v or None)) for k, v in data.items()}
        return data


class Recipe(RecipeBase):
    id: int
    times_made: int
    last_made_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    ingredients: list[RecipeIngredient] = Field(default_factory=list)


class RecipeUpdate(RecipeConfig):
    name: str | None = None
    description: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    total_time_minutes: int | None = None
    servings: int | None = None
    difficulty: str | None = None
    cuisine: str | None = None
    meal_type: str | None = None
    tags: list[str] | None = None
    instructions: str | None = None
    notes: str | None = None
    rating: int | None = None
    ingredients: list[RecipeIngredientCreate] | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class RecipeIngredientSearchResult(RecipeConfig):
    """A recipe plus how many of the user-supplied ingredients it matched."""

    recipe: Recipe
    coverage: int
    total_ingredients: int


class RecipeSuggestionRequest(RecipeConfig):
    have: list[str] = Field(default_factory=list)
    want: str | None = None
    count: int = 3


class RecipeCandidate(RecipeConfig):
    """An AI-generated recipe candidate — same shape as RecipeCreate plus a mandatory source_url."""

    name: str
    description: str | None = None
    source_url: str
    source_name: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    total_time_minutes: int | None = None
    servings: int = 4
    difficulty: str | None = None
    cuisine: str | None = None
    meal_type: str | None = None
    tags: list[str] | None = None
    instructions: str
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeSuggestionResponse(RecipeConfig):
    candidates: list[RecipeCandidate]


class RecipeRatingBreakdown(RecipeConfig):
    rating: int
    count: int


class RecipeCategoryBreakdown(RecipeConfig):
    name: str
    count: int
    avg_rating: float | None = None
    total_times_made: int = 0


class RecipeStats(RecipeConfig):
    total_recipes: int
    total_times_cooked: int
    average_rating: float | None
    unique_cuisines: int
    rating_breakdown: list[RecipeRatingBreakdown]
    cuisine_breakdown: list[RecipeCategoryBreakdown]
    meal_type_breakdown: list[RecipeCategoryBreakdown]
    most_made: list[Recipe]
    highest_rated: list[Recipe]
    untried: list[Recipe]


class CookingTechniqueBase(RecipeConfig):
    name: str
    category: str
    summary: str
    body: str
    why_it_works: str | None = None
    common_pitfalls: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    tags: list[str] | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class CookingTechniqueCreate(CookingTechniqueBase):
    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (v if isinstance(v, list | dict | bool | int | float) else (v or None)) for k, v in data.items()}
        return data


class CookingTechnique(CookingTechniqueBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime


class CookingTechniqueUpdate(RecipeConfig):
    name: str | None = None
    category: str | None = None
    summary: str | None = None
    body: str | None = None
    why_it_works: str | None = None
    common_pitfalls: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    tags: list[str] | None = None
    rating: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class CookingTechniqueCategoryBreakdown(RecipeConfig):
    name: str
    count: int


# =============================================================================
# URL IMPORT — classify and save recipes and/or techniques from a single URL.
# =============================================================================


UrlImportKind = Literal['recipe', 'technique', 'both']


class UrlImportRequest(RecipeConfig):
    url: str
    hint: Literal['auto', 'recipe', 'technique', 'both'] = 'auto'


class UrlImportCandidate(RecipeConfig):
    """Classifier output / user-reviewed save payload for a URL ingest.

    When `kind='both'`, both `recipe` and `technique` are populated and
    `technique_mention` carries a one-line note the save endpoint appends to
    `recipe.notes` to preserve the "these two records came from the same source"
    signal without a database link.
    """

    kind: UrlImportKind
    recipe: RecipeCandidate | None = None
    technique: CookingTechniqueCreate | None = None
    technique_mention: str | None = None

    @model_validator(mode='after')
    def payload_matches_kind(self):
        if self.kind == 'recipe' and self.recipe is None:
            raise ValueError('kind=recipe requires a recipe payload')
        if self.kind == 'technique' and self.technique is None:
            raise ValueError('kind=technique requires a technique payload')
        if self.kind == 'both' and (self.recipe is None or self.technique is None):
            raise ValueError('kind=both requires both recipe and technique payloads')
        return self


class UrlImportResponse(RecipeConfig):
    candidate: UrlImportCandidate


class UrlImportSaveResult(RecipeConfig):
    """Returned by the save endpoint after persistence."""

    recipe: Recipe | None = None
    technique: CookingTechnique | None = None
