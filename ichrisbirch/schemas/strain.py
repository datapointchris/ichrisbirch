from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

# The four array columns are NOT NULL DEFAULT '{}', so a null arriving on the
# wire would reach the column as None and fail the insert. Normalizing here
# means a client may omit a list, send null, or send [] and get the same row.
ARRAY_FIELDS = ('effects', 'flavors', 'terpenes', 'tags')


class StrainConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrainBase(StrainConfig):
    name: str
    breeder: str | None = None
    lineage: str | None = None
    strain_type: str | None = None
    status: str = 'want_to_try'
    thc_percent: float | None = Field(default=None, ge=0, le=100)
    cbd_percent: float | None = Field(default=None, ge=0, le=100)
    rating: int | None = Field(default=None, ge=1, le=10)
    effects: list[str] = Field(default_factory=list)
    flavors: list[str] = Field(default_factory=list)
    terpenes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None
    review: str | None = None
    last_tried_date: date | None = None

    @field_validator(*ARRAY_FIELDS, mode='before')
    @classmethod
    def none_to_empty_list(cls, value):
        return [] if value is None else value


class StrainCreate(StrainBase):
    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (v if isinstance(v, list | dict | bool | int | float) else (v or None)) for k, v in data.items()}
        return data


class Strain(StrainBase):
    id: int
    created_at: datetime
    updated_at: datetime


class StrainUpdate(StrainConfig):
    name: str | None = None
    breeder: str | None = None
    lineage: str | None = None
    strain_type: str | None = None
    status: str | None = None
    thc_percent: float | None = Field(default=None, ge=0, le=100)
    cbd_percent: float | None = Field(default=None, ge=0, le=100)
    rating: int | None = Field(default=None, ge=1, le=10)
    effects: list[str] | None = None
    flavors: list[str] | None = None
    terpenes: list[str] | None = None
    tags: list[str] | None = None
    source: str | None = None
    notes: str | None = None
    review: str | None = None
    last_tried_date: date | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data

    @field_validator(*ARRAY_FIELDS, mode='before')
    @classmethod
    def none_to_empty_list(cls, value):
        """A null array clears the column rather than failing the update.

        `exclude_unset=True` already drops an array the caller never mentioned,
        so reaching here means the caller named it.
        """
        return [] if value is None else value


class StrainVocabularyEntry(StrainConfig):
    name: str
    count: int


class StrainVocabulary(StrainConfig):
    """Every defined value in each vocabulary, whether or not a strain uses it.

    Counted with a left join rather than read off the strains, so "what can I
    record?" has an answer before anything has been recorded.
    """

    types: list[StrainVocabularyEntry]
    statuses: list[StrainVocabularyEntry]
    effects: list[StrainVocabularyEntry]
    flavors: list[StrainVocabularyEntry]
    terpenes: list[StrainVocabularyEntry]
