import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.services.row_limit import RowLimit
from ichrisbirch.services.row_limit import apply_row_limit

logger = structlog.get_logger()
router = APIRouter()

# Every field whose values come from a lookup table, mapped to the column that
# holds them. `strain_type` and `status` also carry a real foreign key; the
# three arrays cannot, because Postgres does not reference a table from an
# array element.
VOCABULARIES: dict[str, InstrumentedAttribute] = {
    'strain_type': models.StrainType.name,
    'status': models.StrainStatus.name,
    'effects': models.StrainEffect.name,
    'flavors': models.StrainFlavor.name,
    'terpenes': models.StrainTerpene.name,
}


def _reject_unknown_vocabulary(session: Session, data: dict) -> None:
    """Refuse a write naming a value no lookup table carries.

    The foreign keys would catch `strain_type` and `status` on their own, but as
    an IntegrityError rather than a message naming what would have worked. The
    arrays have nothing catching them at all, and a typo there is invisible: the
    row saves, and no filter ever finds it again.
    """
    problems = []
    for field, lookup in VOCABULARIES.items():
        submitted = data.get(field)
        if not submitted:
            continue
        values = submitted if isinstance(submitted, list) else [submitted]
        known = set(session.scalars(select(lookup)).all())
        if unknown := sorted(set(values) - known):
            problems.append(f'{field}: {", ".join(unknown)} is not known — use one of {", ".join(sorted(known))}')
    if problems:
        logger.debug('strain_vocabulary_rejected', problems=problems)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='; '.join(problems))


def _scalar_counts(session: Session, column: InstrumentedAttribute) -> dict[str, int]:
    rows = session.execute(select(column, func.count(models.Strain.id)).where(column.isnot(None)).group_by(column)).all()
    return {name: count for name, count in rows}


def _array_counts(session: Session, column: InstrumentedAttribute) -> dict[str, int]:
    """Count how many strains carry each value of an array column."""
    value = func.unnest(column).label('value')
    rows = session.execute(select(value, func.count()).select_from(models.Strain).group_by(value)).all()
    return {name: count for name, count in rows}


def _entries(session: Session, lookup: InstrumentedAttribute, counts: dict[str, int]) -> list[schemas.StrainVocabularyEntry]:
    names = session.scalars(select(lookup).order_by(lookup.asc())).all()
    return [schemas.StrainVocabularyEntry(name=name, count=counts.get(name, 0)) for name in names]


@router.get('/', response_model=list[schemas.Strain], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    strain_type: str | None = Query(None),
    strain_status: str | None = Query(None, alias='status'),
    effect: str | None = Query(None),
    flavor: str | None = Query(None),
    rating_min: int | None = Query(None, ge=1, le=10),
    limit: RowLimit = None,
):
    """List the catalog by name, narrowed by type, status, a single effect or flavor, and a rating floor.

    `limit` caps last, so it takes the first names of whatever the filters left
    rather than filtering an already-capped slice.
    """
    query = select(models.Strain).order_by(models.Strain.name.asc())
    if strain_type:
        query = query.filter(models.Strain.strain_type == strain_type)
    if strain_status:
        query = query.filter(models.Strain.status == strain_status)
    if effect:
        query = query.filter(models.Strain.effects.contains([effect]))
    if flavor:
        query = query.filter(models.Strain.flavors.contains([flavor]))
    if rating_min is not None:
        query = query.filter(models.Strain.rating >= rating_min)
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.post('/', response_model=schemas.Strain, status_code=status.HTTP_201_CREATED)
async def create(strain: schemas.StrainCreate, session: DbSession):
    data = strain.model_dump()
    _reject_unknown_vocabulary(session, data)
    obj = models.Strain(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    logger.info('strain_created', name=obj.name, strain_type=obj.strain_type, status=obj.status)
    return obj


@router.get('/search/', response_model=list[schemas.Strain], status_code=status.HTTP_200_OK)
async def search(q: str, session: DbSession):
    """Search strains by name, breeder, lineage, notes or tags.

    Whitespace- or comma-separated terms; ILIKE match on any field, OR'd together.
    """
    logger.debug('strain_search', query=q)
    raw_terms = q.split(',') if ',' in q else q.split()
    terms = [f'%{term.strip()}%' for term in raw_terms if term.strip()]
    if not terms:
        return []
    columns = [models.Strain.name, models.Strain.breeder, models.Strain.lineage, models.Strain.notes]
    matches = [column.ilike(term) for column in columns for term in terms]
    matches += [cast(models.Strain.tags, postgresql.TEXT).ilike(term) for term in terms]
    query = select(models.Strain).filter(or_(*matches)).order_by(models.Strain.name.asc())
    return list(session.scalars(query).all())


@router.get('/vocabulary/', response_model=schemas.StrainVocabulary, status_code=status.HTTP_200_OK)
async def vocabulary(session: DbSession):
    """Every value each vocabulary defines, with how many strains carry it.

    Counted outward from the lookup tables rather than inward from the strains,
    so a value nothing uses is still listed and "what can I record?" has an
    answer on an empty catalog.
    """
    return schemas.StrainVocabulary(
        types=_entries(session, models.StrainType.name, _scalar_counts(session, models.Strain.strain_type)),
        statuses=_entries(session, models.StrainStatus.name, _scalar_counts(session, models.Strain.status)),
        effects=_entries(session, models.StrainEffect.name, _array_counts(session, models.Strain.effects)),
        flavors=_entries(session, models.StrainFlavor.name, _array_counts(session, models.Strain.flavors)),
        terpenes=_entries(session, models.StrainTerpene.name, _array_counts(session, models.Strain.terpenes)),
    )


@router.get('/{id}/', response_model=schemas.Strain, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if strain := session.get(models.Strain, id):
        return strain
    raise NotFoundException('strain', id, logger)


@router.patch('/{id}/', response_model=schemas.Strain, status_code=status.HTTP_200_OK)
async def update(id: int, strain_update: schemas.StrainUpdate, session: DbSession):
    strain = session.get(models.Strain, id)
    if strain is None:
        raise NotFoundException('strain', id, logger)

    update_data = strain_update.model_dump(exclude_unset=True)
    logger.debug('strain_update', strain_id=id, update_data=update_data)
    _reject_unknown_vocabulary(session, update_data)
    for attr, value in update_data.items():
        setattr(strain, attr, value)
    session.commit()
    session.refresh(strain)
    return strain


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if strain := session.get(models.Strain, id):
        session.delete(strain)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('strain', id, logger)
