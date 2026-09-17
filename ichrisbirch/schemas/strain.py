import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

# The four array columns are NOT NULL DEFAULT '{}', so a null arriving on the
# wire would reach the column as None and fail the insert. Normalizing here
# means a client may omit a list, send null, or send [] and get the same row.
ARRAY_FIELDS = ('effects', 'flavors', 'terpenes', 'tags')

# The columns a PATCH may leave alone but never empty. Both are NOT NULL, and a
# blank reaching `setattr` fails at the column as a 500 rather than as a message
# naming the field.
REQUIRED_COLUMNS = ('name', 'status')


def blank(value) -> bool:
    """A value that would reach a NOT NULL column as null."""
    return value is None or (isinstance(value, str) and not value.strip())


def deduplicated(value):
    """Drop repeats, keeping each value at its first position.

    A repeat stores twice in the array and counts twice in the vocabulary, and
    nothing downstream has a reason to carry the same descriptor twice.
    """
    return list(dict.fromkeys(value))


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
    last_tried_date: dt.date | None = None

    @field_validator(*ARRAY_FIELDS, mode='before')
    @classmethod
    def normalize_array(cls, value):
        if value is None:
            return []
        return deduplicated(value) if isinstance(value, list) else value


class StrainCreate(StrainBase):
    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (v if isinstance(v, list | dict | bool | int | float) else (v or None)) for k, v in data.items()}
        return data


class Strain(StrainBase):
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime


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
    last_tried_date: dt.date | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        """Blank a nullable column with `''` or null; refuse to blank a required one.

        The refusal runs before the conversion, because the conversion is what
        makes the two indistinguishable: `{"name": ""}` and `{"name": null}`
        both become None, and `exclude_unset=True` keeps the key because the
        caller named it. Omitting the key is how a field is left alone.
        """
        if not isinstance(data, dict):
            return data
        for field in REQUIRED_COLUMNS:
            if field in data and blank(data[field]):
                raise ValueError(f'{field} cannot be blank — omit it to leave it unchanged')
        return {k: (None if v == '' else v) for k, v in data.items()}

    @field_validator(*ARRAY_FIELDS, mode='before')
    @classmethod
    def normalize_array(cls, value):
        """A null array clears the column rather than failing the update.

        `exclude_unset=True` already drops an array the caller never mentioned,
        so reaching here means the caller named it.
        """
        if value is None:
            return []
        return deduplicated(value) if isinstance(value, list) else value


class StrainVocabularyEntry(StrainConfig):
    name: str
    count: int


class StrainVocabulary(StrainConfig):
    """Every value each vocabulary defines, keyed by the field it constrains.

    The lookup table decides the entries, so a value no strain carries is
    present with a count of zero and "what can I record?" has an answer on an
    empty catalog.
    """

    strain_type: list[StrainVocabularyEntry]
    status: list[StrainVocabularyEntry]
    effects: list[StrainVocabularyEntry]
    flavors: list[StrainVocabularyEntry]
    terpenes: list[StrainVocabularyEntry]
