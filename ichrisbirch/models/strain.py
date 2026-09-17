"""Strains, and the five lookup tables that supply their vocabularies.

`strain_type` and `status` are single-valued and carry real foreign keys. The
three descriptor columns hold several values each, and Postgres cannot reference
a table from an array element, so their lookup tables supply the vocabulary
while `api/endpoints/strains.py` enforces it on both reads and writes.

**Four of the five vocabularies are open sets served to the clients**, so adding
a value is an insert here plus a line in `LOOKUP_DATA`, with no client release.
The Vue store and the `icb` CLI both read `GET /strains/vocabulary/`.

**`status` is the exception and is a closed lifecycle.** Its two values are
compiled into both clients, because each one needs a counter, a filter, a row
color and a label that a lookup table carrying only a name cannot supply.
Inserting a third would list and validate, and would get none of those. Adding
a status is a code change in three places, and that is the trade taken.
"""

import datetime as dt

from sqlalchemy import CheckConstraint
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base

STRAIN_TYPES = [
    'cbd',
    'hybrid',
    'indica',
    'indica_dominant',
    'ruderalis',
    'sativa',
    'sativa_dominant',
]

STRAIN_STATUSES = [
    'tried',
    'want_to_try',
]

STRAIN_EFFECTS = [
    'creative',
    'energetic',
    'euphoric',
    'focused',
    'giggly',
    'happy',
    'hungry',
    'relaxed',
    'sleepy',
    'talkative',
    'tingly',
    'uplifted',
]

STRAIN_FLAVORS = [
    'berry',
    'cheese',
    'citrus',
    'coffee',
    'diesel',
    'earthy',
    'floral',
    'grape',
    'mint',
    'pine',
    'skunk',
    'spicy',
    'sweet',
    'tropical',
    'vanilla',
    'woody',
]

STRAIN_TERPENES = [
    'bisabolol',
    'caryophyllene',
    'humulene',
    'limonene',
    'linalool',
    'myrcene',
    'nerolidol',
    'ocimene',
    'pinene',
    'terpinolene',
]


class StrainType(Base):
    """Lookup table for strain classification."""

    __tablename__ = 'strain_types'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class StrainStatus(Base):
    """Lookup table for whether a strain has been tried."""

    __tablename__ = 'strain_statuses'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class StrainEffect(Base):
    """Lookup table for the effects a strain produces."""

    __tablename__ = 'strain_effects'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class StrainFlavor(Base):
    """Lookup table for a strain's taste and aroma notes."""

    __tablename__ = 'strain_flavors'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class StrainTerpene(Base):
    """Lookup table for the terpenes present in a strain."""

    __tablename__ = 'strain_terpenes'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Strain(Base):
    __tablename__ = 'strains'
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating BETWEEN 1 AND 10)', name='rating_range'),
        # A catalog row needs a natural key an import can upsert on. NULLS NOT
        # DISTINCT so two rows named the same with no breeder collide — Postgres
        # treats nulls as distinct by default, and the unknown breeder is the
        # common case.
        UniqueConstraint('name', 'breeder', postgresql_nulls_not_distinct=True),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    breeder: Mapped[str | None] = mapped_column(Text, nullable=True)
    lineage: Mapped[str | None] = mapped_column(Text, nullable=True)
    strain_type: Mapped[str | None] = mapped_column(Text, ForeignKey('strain_types.name'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(Text, ForeignKey('strain_statuses.name'), server_default='want_to_try', nullable=False, index=True)
    thc_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    cbd_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effects: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), server_default='{}', nullable=False)
    flavors: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), server_default='{}', nullable=False)
    terpenes: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), server_default='{}', nullable=False)
    tags: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), server_default='{}', nullable=False)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_tried_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f'Strain(id={self.id!r}, name={self.name!r}, strain_type={self.strain_type!r}, status={self.status!r})'
