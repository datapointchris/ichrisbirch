import structlog
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import cast
from sqlalchemy import false
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

# The column each vocabulary lives in, keyed by the record field it constrains.
# What the vocabularies are for is `models/strain.py`.
WRITE_VOCABULARIES: dict[str, InstrumentedAttribute] = {
    'strain_type': models.StrainType.name,
    'status': models.StrainStatus.name,
    'effects': models.StrainEffect.name,
    'flavors': models.StrainFlavor.name,
    'terpenes': models.StrainTerpene.name,
}

# The same vocabularies keyed by the query parameter that selects on them. The
# three descriptor filters are singular because a filter asks for one value
# inside a list.
FILTER_VOCABULARIES: dict[str, InstrumentedAttribute] = {
    'strain_type': models.StrainType.name,
    'status': models.StrainStatus.name,
    'effect': models.StrainEffect.name,
    'flavor': models.StrainFlavor.name,
    'terpene': models.StrainTerpene.name,
}


def reject_unknown_vocabulary(session: Session, submitted: dict, vocabularies: dict[str, InstrumentedAttribute]) -> None:
    """Refuse a value no lookup table carries, naming what would have worked.

    Both doors call this. A write that gets it wrong saves a row no filter finds
    again, and a read that gets it wrong answers 200 with an empty list, which
    reads as an empty catalog rather than as a typo. The foreign keys catch
    `strain_type` and `status` on a write, but as an IntegrityError rather than
    a message, and they reach neither the arrays nor any read.
    """
    problems = []
    for field, lookup in vocabularies.items():
        submitted_value = submitted.get(field)
        if not submitted_value:
            continue
        values = submitted_value if isinstance(submitted_value, list) else [submitted_value]
        known = set(session.scalars(select(lookup)).all())
        if unknown := sorted(set(values) - known):
            problems.append(f'{field}: {", ".join(unknown)} is not known — use one of {", ".join(sorted(known))}')
    if problems:
        logger.debug('strain_vocabulary_rejected', problems=problems)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='; '.join(problems))


def reject_duplicate_natural_key(session: Session, name: str, breeder: str | None, exclude_id: int | None = None) -> None:
    """Refuse a second row carrying the same (name, breeder).

    The unique index is the guarantee. This is what turns it into a 409 naming
    the row already holding the key, rather than an IntegrityError the handler
    reports as a 500. `IS NOT DISTINCT FROM` matches the index's NULLS NOT
    DISTINCT, so two rows with no breeder collide here exactly as they do there.
    """
    query = select(models.Strain.id).where(
        models.Strain.name == name,
        models.Strain.breeder.is_not_distinct_from(breeder),
    )
    if exclude_id is not None:
        query = query.where(models.Strain.id != exclude_id)
    if existing := session.scalar(query):
        logger.debug('strain_duplicate_rejected', name=name, breeder=breeder, existing_id=existing)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'{name} is already in the catalog under that breeder, as id {existing}',
        )


def scalar_counts(session: Session, column: InstrumentedAttribute) -> dict[str, int]:
    rows = session.execute(select(column, func.count(models.Strain.id)).where(column.isnot(None)).group_by(column)).all()
    return {name: count for name, count in rows}


def array_counts(session: Session, column: InstrumentedAttribute) -> dict[str, int]:
    """Count the strains carrying each value of an array column.

    `distinct` on the id rather than a row count, so a value repeated inside one
    strain's array counts that strain once. The schema deduplicates on write;
    this holds for rows that predate it or arrive another way.
    """
    value = func.unnest(column).label('value')
    rows = session.execute(select(value, func.count(func.distinct(models.Strain.id))).select_from(models.Strain).group_by(value)).all()
    return {name: count for name, count in rows}


def vocabulary_entries(session: Session, lookup: InstrumentedAttribute, counts: dict[str, int]) -> list[schemas.StrainVocabularyEntry]:
    """Every value the lookup table defines, in name order, with its count."""
    names = session.scalars(select(lookup).order_by(lookup.asc())).all()
    return [schemas.StrainVocabularyEntry(name=name, count=counts.get(name, 0)) for name in names]


@router.get('/', response_model=list[schemas.Strain], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    strain_type: str | None = Query(None),
    strain_status: str | None = Query(None, alias='status'),
    effect: str | None = Query(None),
    flavor: str | None = Query(None),
    terpene: str | None = Query(None),
    rating_min: int | None = Query(None, ge=1, le=10),
    q: str | None = Query(None),
    limit: RowLimit = None,
):
    """List the catalog by name, narrowed by type, status, one descriptor of each kind, a rating floor and a search.

    Every filter value is checked against its lookup table first, so a misspelled
    one is a 422 naming the valid values rather than an empty list that reads as
    an empty catalog.

    `q` searches name, breeder, lineage, notes and tags, and narrows alongside
    the filters rather than from its own route. A separate `/search/` would be a
    second collection read that has to grow every filter and the limit again.

    `limit` caps last, so it takes the first names of whatever the filters left
    rather than filtering an already-capped slice.
    """
    reject_unknown_vocabulary(
        session,
        {'strain_type': strain_type, 'status': strain_status, 'effect': effect, 'flavor': flavor, 'terpene': terpene},
        FILTER_VOCABULARIES,
    )

    query = select(models.Strain).order_by(models.Strain.name.asc())
    if strain_type:
        query = query.filter(models.Strain.strain_type == strain_type)
    if strain_status:
        query = query.filter(models.Strain.status == strain_status)
    if effect:
        query = query.filter(models.Strain.effects.contains([effect]))
    if flavor:
        query = query.filter(models.Strain.flavors.contains([flavor]))
    if terpene:
        query = query.filter(models.Strain.terpenes.contains([terpene]))
    if rating_min is not None:
        query = query.filter(models.Strain.rating >= rating_min)
    if q:
        query = query.filter(search_clause(q))
    return list(session.scalars(apply_row_limit(query, limit)).all())


@router.post('/', response_model=schemas.Strain, status_code=status.HTTP_201_CREATED)
async def create(strain: schemas.StrainCreate, session: DbSession):
    data = strain.model_dump()
    reject_unknown_vocabulary(session, data, WRITE_VOCABULARIES)
    reject_duplicate_natural_key(session, data['name'], data.get('breeder'))
    obj = models.Strain(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    logger.info('strain_created', name=obj.name, strain_type=obj.strain_type, status=obj.status)
    return obj


def search_clause(q: str):
    """Match `q` against name, breeder, lineage, notes or tags.

    Whitespace- or comma-separated terms; ILIKE on any field, OR'd together. A
    query of only whitespace matches no row rather than every row.
    """
    raw_terms = q.split(',') if ',' in q else q.split()
    terms = [f'%{term.strip()}%' for term in raw_terms if term.strip()]
    if not terms:
        return false()

    columns = [models.Strain.name, models.Strain.breeder, models.Strain.lineage, models.Strain.notes]
    matches = [cast(models.Strain.tags, postgresql.TEXT).ilike(term) for term in terms]
    for column in columns:
        matches += [column.ilike(term) for term in terms]
    return or_(*matches)


@router.get('/vocabulary/', response_model=schemas.StrainVocabulary, status_code=status.HTTP_200_OK)
async def vocabulary(session: DbSession):
    """Every value each vocabulary defines, with how many strains carry it.

    Read outward from the lookup tables rather than inward from the strains, so
    a value nothing uses is listed with a count of zero.
    """
    return schemas.StrainVocabulary(
        strain_type=vocabulary_entries(session, models.StrainType.name, scalar_counts(session, models.Strain.strain_type)),
        status=vocabulary_entries(session, models.StrainStatus.name, scalar_counts(session, models.Strain.status)),
        effects=vocabulary_entries(session, models.StrainEffect.name, array_counts(session, models.Strain.effects)),
        flavors=vocabulary_entries(session, models.StrainFlavor.name, array_counts(session, models.Strain.flavors)),
        terpenes=vocabulary_entries(session, models.StrainTerpene.name, array_counts(session, models.Strain.terpenes)),
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
    reject_unknown_vocabulary(session, update_data, WRITE_VOCABULARIES)
    # Checked against what the row would become, since a patch can move either
    # half of the key onto another row's.
    if 'name' in update_data or 'breeder' in update_data:
        reject_duplicate_natural_key(
            session,
            update_data.get('name', strain.name),
            update_data.get('breeder', strain.breeder),
            exclude_id=id,
        )
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
