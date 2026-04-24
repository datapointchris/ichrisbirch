from datetime import UTC
from datetime import datetime

import httpx
import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.services import url_ingest
from ichrisbirch.services.url_ingest import ClassifierOutputError
from ichrisbirch.util import slugify

logger = structlog.get_logger()
router = APIRouter()


def _unique_cooking_technique_slug(session: Session, base_slug: str) -> str:
    """Append -2, -3, ... if `base_slug` already exists."""
    existing = set(session.scalars(select(models.CookingTechnique.slug).where(models.CookingTechnique.slug.like(f'{base_slug}%'))).all())
    if base_slug not in existing:
        return base_slug
    counter = 2
    while f'{base_slug}-{counter}' in existing:
        counter += 1
    return f'{base_slug}-{counter}'


def _load_recipe(session: Session, recipe_id: int) -> models.Recipe | None:
    query = select(models.Recipe).options(selectinload(models.Recipe.ingredients)).where(models.Recipe.id == recipe_id)
    return session.scalar(query)


def _scaled_recipe_response(recipe: models.Recipe, servings: int | None) -> schemas.Recipe:
    """Build a Recipe response and, if `servings` differs from the base, include scaled quantities."""
    response = schemas.Recipe.model_validate(recipe)
    if servings is None or recipe.servings in (servings, 0):
        return response
    factor = servings / recipe.servings
    for ing_model, ing_out in zip(recipe.ingredients, response.ingredients, strict=False):
        ing_out.scaled_quantity = round(ing_model.quantity * factor, 4) if ing_model.quantity is not None else None
    return response


@router.get('/', response_model=list[schemas.Recipe], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    cuisine: str | None = None,
    meal_type: str | None = None,
    difficulty: str | None = None,
    rating_min: int | None = Query(None, ge=1, le=5),
    max_total_time: int | None = Query(None, ge=0),
):
    query = select(models.Recipe).options(selectinload(models.Recipe.ingredients)).order_by(models.Recipe.name.asc())
    if cuisine:
        query = query.filter(models.Recipe.cuisine == cuisine)
    if meal_type:
        query = query.filter(models.Recipe.meal_type == meal_type)
    if difficulty:
        query = query.filter(models.Recipe.difficulty == difficulty)
    if rating_min is not None:
        query = query.filter(models.Recipe.rating >= rating_min)
    if max_total_time is not None:
        query = query.filter(models.Recipe.total_time_minutes <= max_total_time)
    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Recipe, status_code=status.HTTP_201_CREATED)
async def create(recipe: schemas.RecipeCreate, session: DbSession):
    ingredients_data = recipe.ingredients
    recipe_data = recipe.model_dump(exclude={'ingredients'})
    obj = models.Recipe(**recipe_data)
    for idx, ing in enumerate(ingredients_data):
        ing_dict = ing.model_dump()
        # Preserve provided position if non-default, otherwise use list index
        if ing_dict.get('position', 0) == 0:
            ing_dict['position'] = idx
        obj.ingredients.append(models.RecipeIngredient(**ing_dict))
    session.add(obj)
    session.commit()
    session.refresh(obj)
    reloaded = _load_recipe(session, obj.id)
    return reloaded


@router.get('/search/', response_model=list[schemas.Recipe], status_code=status.HTTP_200_OK)
async def search(q: str, session: DbSession):
    """Search recipes by name, tags, or instructions.

    Follows the books/articles pattern: split on comma (for phrases) or whitespace,
    ILIKE across multiple fields, OR'd together.
    """
    logger.debug('recipe_search', query=q)
    raw_terms = q.split(',') if ',' in q else q.split()
    search_terms = [f'%{term.strip()}%' for term in raw_terms if term.strip()]
    if not search_terms:
        return []
    name_matches = [models.Recipe.name.ilike(term) for term in search_terms]
    instruction_matches = [models.Recipe.instructions.ilike(term) for term in search_terms]
    tag_matches = [cast(models.Recipe.tags, postgresql.TEXT).ilike(term) for term in search_terms]
    query = (
        select(models.Recipe)
        .options(selectinload(models.Recipe.ingredients))
        .filter(or_(*(name_matches + instruction_matches + tag_matches)))
        .order_by(models.Recipe.name.asc())
    )
    return list(session.scalars(query).all())


@router.get(
    '/search-by-ingredients/',
    response_model=list[schemas.RecipeIngredientSearchResult],
    status_code=status.HTTP_200_OK,
)
async def search_by_ingredients(
    session: DbSession,
    have: str = Query(..., description='Comma-separated list of ingredients the user has'),
    match: str = Query('any', pattern='^(any|all)$'),
):
    """Find recipes whose ingredients match the user-supplied list.

    `match=any` — return recipes containing ANY of the listed ingredients, ranked by
    coverage (how many matched) descending.
    `match=all` — only return recipes where every listed ingredient is present.

    Matching is case-insensitive substring ILIKE on `recipe_ingredients.item`, so
    'chicken' matches 'boneless chicken breast'.
    """
    terms = [t.strip() for t in have.split(',') if t.strip()]
    if not terms:
        return []

    # For each term, count distinct recipes where any ingredient item ILIKEs it.
    # Build a CASE-based coverage counter: for each recipe, sum 1 per term matched.
    per_term_hit = [
        func.max(case((models.RecipeIngredient.item.ilike(f'%{term}%'), 1), else_=0)).label(f'hit_{i}') for i, term in enumerate(terms)
    ]

    # First aggregation: for each recipe, did each term match at least once?
    any_conditions = or_(*[models.RecipeIngredient.item.ilike(f'%{term}%') for term in terms])

    subq = (
        select(models.RecipeIngredient.recipe_id.label('recipe_id'), *per_term_hit)
        .where(any_conditions)
        .group_by(models.RecipeIngredient.recipe_id)
        .subquery()
    )

    total_count_subq = (
        select(
            models.RecipeIngredient.recipe_id.label('recipe_id'),
            func.count(models.RecipeIngredient.id).label('total_ingredients'),
        )
        .group_by(models.RecipeIngredient.recipe_id)
        .subquery()
    )

    hit_sum = sum(getattr(subq.c, f'hit_{i}') for i in range(len(terms)))

    query = (
        select(models.Recipe, hit_sum.label('coverage'), total_count_subq.c.total_ingredients)
        .join(subq, subq.c.recipe_id == models.Recipe.id)
        .join(total_count_subq, total_count_subq.c.recipe_id == models.Recipe.id)
        .options(selectinload(models.Recipe.ingredients))
        .order_by(hit_sum.desc(), models.Recipe.name.asc())
    )

    if match == 'all':
        query = query.where(hit_sum == len(terms))

    results = session.execute(query).all()
    return [
        schemas.RecipeIngredientSearchResult(
            recipe=schemas.Recipe.model_validate(recipe),
            coverage=int(coverage),
            total_ingredients=int(total),
        )
        for recipe, coverage, total in results
    ]


@router.get('/stats/', response_model=schemas.RecipeStats, status_code=status.HTTP_200_OK)
async def stats(session: DbSession):
    total_recipes = session.scalar(select(func.count(models.Recipe.id))) or 0
    total_times_cooked = session.scalar(select(func.coalesce(func.sum(models.Recipe.times_made), 0))) or 0
    average_rating = session.scalar(select(func.avg(models.Recipe.rating)))
    unique_cuisines = session.scalar(select(func.count(func.distinct(models.Recipe.cuisine))).where(models.Recipe.cuisine.isnot(None))) or 0

    rating_rows = session.execute(
        select(models.Recipe.rating, func.count(models.Recipe.id))
        .where(models.Recipe.rating.isnot(None))
        .group_by(models.Recipe.rating)
        .order_by(models.Recipe.rating.asc())
    ).all()
    rating_breakdown = [schemas.RecipeRatingBreakdown(rating=r, count=c) for r, c in rating_rows]

    def _category_breakdown(column) -> list[schemas.RecipeCategoryBreakdown]:
        rows = session.execute(
            select(
                column,
                func.count(models.Recipe.id),
                func.avg(models.Recipe.rating),
                func.coalesce(func.sum(models.Recipe.times_made), 0),
            )
            .where(column.isnot(None))
            .group_by(column)
            .order_by(func.count(models.Recipe.id).desc())
        ).all()
        return [
            schemas.RecipeCategoryBreakdown(
                name=name,
                count=count,
                avg_rating=float(avg) if avg is not None else None,
                total_times_made=int(times_made),
            )
            for name, count, avg, times_made in rows
        ]

    most_made = list(
        session.scalars(
            select(models.Recipe)
            .options(selectinload(models.Recipe.ingredients))
            .where(models.Recipe.times_made > 0)
            .order_by(models.Recipe.times_made.desc())
            .limit(5)
        ).all()
    )
    highest_rated = list(
        session.scalars(
            select(models.Recipe)
            .options(selectinload(models.Recipe.ingredients))
            .where(models.Recipe.rating.isnot(None))
            .order_by(models.Recipe.rating.desc(), models.Recipe.times_made.desc())
            .limit(5)
        ).all()
    )
    untried = list(
        session.scalars(
            select(models.Recipe)
            .options(selectinload(models.Recipe.ingredients))
            .where(models.Recipe.times_made == 0)
            .order_by(models.Recipe.created_at.desc())
            .limit(5)
        ).all()
    )

    return schemas.RecipeStats(
        total_recipes=total_recipes,
        total_times_cooked=total_times_cooked,
        average_rating=float(average_rating) if average_rating is not None else None,
        unique_cuisines=unique_cuisines,
        rating_breakdown=rating_breakdown,
        cuisine_breakdown=_category_breakdown(models.Recipe.cuisine),
        meal_type_breakdown=_category_breakdown(models.Recipe.meal_type),
        most_made=[schemas.Recipe.model_validate(r) for r in most_made],
        highest_rated=[schemas.Recipe.model_validate(r) for r in highest_rated],
        untried=[schemas.Recipe.model_validate(r) for r in untried],
    )


@router.post('/ai-suggest/', response_model=schemas.RecipeSuggestionResponse, status_code=status.HTTP_200_OK)
async def ai_suggest(
    request: schemas.RecipeSuggestionRequest,
    settings: Settings = Depends(get_settings),
):
    """Ask Claude (with web_search) to find recipes matching the user's inputs.

    Returns candidates WITHOUT saving — the user reviews and saves via /ai-save/.
    """
    assistant = AnthropicAssistant(
        name='Recipe Suggestions',
        system_prompt=settings.ai.prompts.recipe_suggestions,
        settings=settings,
        tools=[{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 5}],
    )
    user_message = (
        f'have: {", ".join(request.have) if request.have else "(none specified)"}\n'
        f'want: {request.want or "(no preference)"}\n'
        f'count: {request.count}'
    )
    text = assistant.generate(user_message, max_tokens=8192)
    parsed = AnthropicAssistant.parse_json(text)
    if isinstance(parsed, dict) and 'candidates' in parsed:
        candidates_raw = parsed['candidates']
    elif isinstance(parsed, list):
        candidates_raw = parsed
    else:
        logger.error('recipe_suggestion_parse_failed', payload_preview=text[:500])
        return schemas.RecipeSuggestionResponse(candidates=[])
    candidates = [schemas.RecipeCandidate.model_validate(c) for c in candidates_raw]
    return schemas.RecipeSuggestionResponse(candidates=candidates)


@router.post('/ai-save/', response_model=schemas.Recipe, status_code=status.HTTP_201_CREATED)
async def ai_save(candidate: schemas.RecipeCandidate, session: DbSession):
    """Save an AI-generated candidate to the recipes table."""
    payload = candidate.model_dump()
    ingredients_data = payload.pop('ingredients', [])
    obj = models.Recipe(**payload)
    for idx, ing_dict in enumerate(ingredients_data):
        if ing_dict.get('position', 0) == 0:
            ing_dict['position'] = idx
        obj.ingredients.append(models.RecipeIngredient(**ing_dict))
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return _load_recipe(session, obj.id)


# =============================================================================
# URL IMPORT — classify a YouTube or article URL into recipe/technique candidates.
# =============================================================================


@router.post('/import-from-url/', response_model=schemas.UrlImportResponse, status_code=status.HTTP_200_OK)
async def import_from_url(
    request: schemas.UrlImportRequest,
    session: DbSession,
    settings: Settings = Depends(get_settings),
):
    """Extract content from a URL, classify via Claude, and return candidate(s) for review.

    Returns 409 if the URL is already ingested as a recipe or a technique (checks
    both tables — a single URL can legitimately back either entity). Returns 502 if
    the classifier output fails to validate against the candidate schema, with the
    raw output embedded for prompt-drift observability.
    """
    url = request.url
    existing_recipe = session.scalar(select(models.Recipe).where(models.Recipe.source_url == url))
    existing_technique = session.scalar(select(models.CookingTechnique).where(models.CookingTechnique.source_url == url))
    if existing_recipe is not None or existing_technique is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'message': 'URL already ingested',
                'recipe_id': existing_recipe.id if existing_recipe else None,
                'technique_id': existing_technique.id if existing_technique else None,
            },
        )

    try:
        content = url_ingest.extract_content_for_classifier(url, settings)
    except httpx.HTTPError as e:
        logger.error('url_content_fetch_failed', url=url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Could not fetch URL content: {e}',
        ) from e

    try:
        candidate = url_ingest.classify_url_content(url, request.hint, content, settings)
    except ClassifierOutputError as e:
        logger.error('url_import_classifier_validation_failed', url=url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={'message': str(e), 'raw_classifier_output': e.raw_output},
        ) from e

    return schemas.UrlImportResponse(candidate=candidate)


@router.post('/save-url-import/', response_model=schemas.UrlImportSaveResult, status_code=status.HTTP_201_CREATED)
async def save_url_import(candidate: schemas.UrlImportCandidate, session: DbSession):
    """Persist a reviewed URL-import candidate atomically.

    For `kind='both'`, both the recipe and technique are created in one transaction
    and the candidate's `technique_mention` is appended to `recipe.notes` so the
    relationship between the two records stays visible as prose (no link table —
    see Phase 2 rejection in the planning doc).
    """
    recipe_obj: models.Recipe | None = None
    technique_obj: models.CookingTechnique | None = None

    if candidate.recipe is not None:
        recipe_data = candidate.recipe.model_dump()
        ingredients_data = recipe_data.pop('ingredients', [])
        if candidate.kind == 'both' and candidate.technique_mention:
            existing_notes = recipe_data.get('notes')
            recipe_data['notes'] = f'{existing_notes}\n\n{candidate.technique_mention}' if existing_notes else candidate.technique_mention
        recipe_obj = models.Recipe(**recipe_data)
        for idx, ing_dict in enumerate(ingredients_data):
            if ing_dict.get('position', 0) == 0:
                ing_dict['position'] = idx
            recipe_obj.ingredients.append(models.RecipeIngredient(**ing_dict))
        session.add(recipe_obj)

    if candidate.technique is not None:
        technique_data = candidate.technique.model_dump()
        technique_data['slug'] = _unique_cooking_technique_slug(session, slugify(technique_data['name']))
        technique_obj = models.CookingTechnique(**technique_data)
        session.add(technique_obj)

    session.commit()

    result_recipe = None
    result_technique = None
    if recipe_obj is not None:
        session.refresh(recipe_obj)
        result_recipe = schemas.Recipe.model_validate(_load_recipe(session, recipe_obj.id))
    if technique_obj is not None:
        session.refresh(technique_obj)
        result_technique = schemas.CookingTechnique.model_validate(technique_obj)
    return schemas.UrlImportSaveResult(recipe=result_recipe, technique=result_technique)


# =============================================================================
# COOKING TECHNIQUES
# =============================================================================
# Cooking techniques are part of the Recipes domain — reusable cooking patterns
# (e.g. "3:1 vinaigrette ratio", "caramelize tomato paste before liquids") that
# multiple recipes can reference. Served as sub-resources under /recipes/cooking-techniques/.


@router.get('/cooking-techniques/', response_model=list[schemas.CookingTechnique], status_code=status.HTTP_200_OK)
async def list_cooking_techniques(
    session: DbSession,
    category: str | None = None,
    rating_min: int | None = Query(None, ge=1, le=5),
):
    query = select(models.CookingTechnique).order_by(models.CookingTechnique.name.asc())
    if category:
        query = query.filter(models.CookingTechnique.category == category)
    if rating_min is not None:
        query = query.filter(models.CookingTechnique.rating >= rating_min)
    return list(session.scalars(query).all())


@router.post('/cooking-techniques/', response_model=schemas.CookingTechnique, status_code=status.HTTP_201_CREATED)
async def create_cooking_technique(technique: schemas.CookingTechniqueCreate, session: DbSession):
    data = technique.model_dump()
    data['slug'] = _unique_cooking_technique_slug(session, slugify(data['name']))
    obj = models.CookingTechnique(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/cooking-techniques/search/', response_model=list[schemas.CookingTechnique], status_code=status.HTTP_200_OK)
async def search_cooking_techniques(q: str, session: DbSession):
    """Search cooking techniques by name, summary, body, or tags.

    Whitespace- or comma-separated terms; ILIKE match on any field, OR'd together.
    """
    logger.debug('cooking_technique_search', query=q)
    raw_terms = q.split(',') if ',' in q else q.split()
    search_terms = [f'%{term.strip()}%' for term in raw_terms if term.strip()]
    if not search_terms:
        return []
    name_matches = [models.CookingTechnique.name.ilike(term) for term in search_terms]
    summary_matches = [models.CookingTechnique.summary.ilike(term) for term in search_terms]
    body_matches = [models.CookingTechnique.body.ilike(term) for term in search_terms]
    tag_matches = [cast(models.CookingTechnique.tags, postgresql.TEXT).ilike(term) for term in search_terms]
    query = (
        select(models.CookingTechnique)
        .filter(or_(*(name_matches + summary_matches + body_matches + tag_matches)))
        .order_by(models.CookingTechnique.name.asc())
    )
    return list(session.scalars(query).all())


@router.get(
    '/cooking-techniques/categories/',
    response_model=list[schemas.CookingTechniqueCategoryBreakdown],
    status_code=status.HTTP_200_OK,
)
async def list_cooking_technique_categories(session: DbSession):
    """List all cooking technique categories with counts. Includes zero-count categories so the UI shows every bucket."""
    category_names = list(
        session.scalars(select(models.CookingTechniqueCategory.name).order_by(models.CookingTechniqueCategory.name.asc())).all()
    )
    counts_rows = session.execute(
        select(models.CookingTechnique.category, func.count(models.CookingTechnique.id)).group_by(models.CookingTechnique.category)
    ).all()
    counts = {name: count for name, count in counts_rows}
    return [schemas.CookingTechniqueCategoryBreakdown(name=name, count=counts.get(name, 0)) for name in category_names]


@router.get('/cooking-techniques/slug/{slug}/', response_model=schemas.CookingTechnique, status_code=status.HTTP_200_OK)
async def read_cooking_technique_by_slug(slug: str, session: DbSession):
    technique = session.scalar(select(models.CookingTechnique).where(models.CookingTechnique.slug == slug))
    if technique is None:
        raise NotFoundException('cooking_technique', slug, logger)
    return technique


@router.get('/cooking-techniques/{id}/', response_model=schemas.CookingTechnique, status_code=status.HTTP_200_OK)
async def read_cooking_technique(id: int, session: DbSession):
    technique = session.get(models.CookingTechnique, id)
    if technique is None:
        raise NotFoundException('cooking_technique', id, logger)
    return technique


@router.delete('/cooking-techniques/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_cooking_technique(id: int, session: DbSession):
    technique = session.get(models.CookingTechnique, id)
    if technique is None:
        raise NotFoundException('cooking_technique', id, logger)
    session.delete(technique)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/cooking-techniques/{id}/', response_model=schemas.CookingTechnique, status_code=status.HTTP_200_OK)
async def update_cooking_technique(id: int, technique_update: schemas.CookingTechniqueUpdate, session: DbSession):
    technique = session.get(models.CookingTechnique, id)
    if technique is None:
        raise NotFoundException('cooking_technique', id, logger)

    update_data = technique_update.model_dump(exclude_unset=True)
    # Slug is server-owned — name changes do not alter the slug (preserves deep links).
    for attr, value in update_data.items():
        setattr(technique, attr, value)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error('cooking_technique_update_failed', id=id, error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    session.refresh(technique)
    return technique


# =============================================================================
# RECIPES (by id)
# =============================================================================


@router.get('/{id}/', response_model=schemas.Recipe, status_code=status.HTTP_200_OK)
async def read_one(
    id: int,
    session: DbSession,
    servings: int | None = Query(None, ge=1, description='Optional scaling — returns scaled_quantity per ingredient'),
):
    recipe = _load_recipe(session, id)
    if recipe is None:
        raise NotFoundException('recipe', id, logger)
    return _scaled_recipe_response(recipe, servings)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    recipe = session.get(models.Recipe, id)
    if recipe is None:
        raise NotFoundException('recipe', id, logger)
    session.delete(recipe)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/{id}/', response_model=schemas.Recipe, status_code=status.HTTP_200_OK)
async def update(id: int, recipe_update: schemas.RecipeUpdate, session: DbSession):
    recipe = _load_recipe(session, id)
    if recipe is None:
        raise NotFoundException('recipe', id, logger)

    update_data = recipe_update.model_dump(exclude_unset=True)
    ingredients_data = update_data.pop('ingredients', None)
    for attr, value in update_data.items():
        setattr(recipe, attr, value)

    if ingredients_data is not None:
        # Replace-all strategy: simpler than diff, sufficient for a modal-based UX.
        recipe.ingredients.clear()
        session.flush()
        for idx, ing in enumerate(ingredients_data):
            if ing.get('position', 0) == 0:
                ing['position'] = idx
            recipe.ingredients.append(models.RecipeIngredient(**ing))

    session.commit()
    session.refresh(recipe)
    return _load_recipe(session, id)


@router.post('/{id}/mark-made/', response_model=schemas.Recipe, status_code=status.HTTP_200_OK)
async def mark_made(id: int, session: DbSession):
    """Increment times_made and set last_made_date to now."""
    recipe = session.get(models.Recipe, id)
    if recipe is None:
        raise NotFoundException('recipe', id, logger)
    recipe.times_made = (recipe.times_made or 0) + 1
    recipe.last_made_date = datetime.now(UTC)
    session.commit()
    return _load_recipe(session, id)
