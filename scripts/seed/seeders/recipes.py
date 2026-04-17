"""Seed recipes with structured ingredients across cuisines and meal types."""

from __future__ import annotations

import random

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.recipe import RECIPE_CUISINES
from ichrisbirch.models.recipe import RECIPE_DIFFICULTIES
from ichrisbirch.models.recipe import RECIPE_MEAL_TYPES
from ichrisbirch.models.recipe import RECIPE_UNITS
from ichrisbirch.models.recipe import Recipe
from ichrisbirch.models.recipe import RecipeCuisine
from ichrisbirch.models.recipe import RecipeDifficulty
from ichrisbirch.models.recipe import RecipeIngredient
from ichrisbirch.models.recipe import RecipeMealType
from ichrisbirch.models.recipe import RecipeUnit
from scripts.seed.base import SeedResult
from scripts.seed.base import random_past_datetime


def _recipe(
    name: str,
    description: str,
    cuisine: str,
    meal_type: str,
    difficulty: str,
    prep: int,
    cook: int,
    servings: int,
    tags: list[str],
    instructions: str,
    ingredients: list[tuple[float | None, str | None, str, str | None]],
    *,
    rating: int | None = None,
    times_made: int = 0,
    source_url: str | None = None,
    source_name: str | None = None,
) -> Recipe:
    total = prep + cook
    recipe = Recipe(
        name=name,
        description=description,
        cuisine=cuisine,
        meal_type=meal_type,
        difficulty=difficulty,
        prep_time_minutes=prep,
        cook_time_minutes=cook,
        total_time_minutes=total,
        servings=servings,
        tags=tags,
        instructions=instructions,
        rating=rating,
        times_made=times_made,
        source_url=source_url,
        source_name=source_name,
        last_made_date=random_past_datetime(180) if times_made > 0 else None,
    )
    for idx, (qty, unit, item, prep_note) in enumerate(ingredients):
        recipe.ingredients.append(RecipeIngredient(position=idx, quantity=qty, unit=unit, item=item, prep_note=prep_note))
    return recipe


RECIPE_BLUEPRINTS: list[dict] = [
    {
        'name': 'Chicken with Lemon Pasta',
        'description': 'Quick one-pot lemon-chicken pasta',
        'cuisine': 'italian',
        'meal_type': 'dinner',
        'difficulty': 'easy',
        'prep': 10,
        'cook': 20,
        'servings': 4,
        'tags': ['quick', 'weeknight', 'pasta'],
        'instructions': (
            'Combine broth, water, lemon peel, lemon juice, honey, and pepper in a saucepan.\n'
            'Bring to a boil, add linguine, reduce heat and simmer 15 minutes.\n'
            'Add chicken, cover and simmer 5 minutes until linguine is tender.'
        ),
        'ingredients': [
            (3, 'cup', 'chicken broth', None),
            (1, 'tbsp', 'honey', None),
            (1, 'cup', 'water', None),
            (0.125, 'tsp', 'black pepper', None),
            (0.5, 'tsp', 'lemon peel', 'grated'),
            (0.5, 'lb', 'linguini', 'uncooked'),
            (9, 'oz', 'chicken breast strips', 'cooked'),
        ],
    },
    {
        'name': 'Amish Baked Oatmeal',
        'description': 'Sweet baked oatmeal breakfast casserole',
        'cuisine': 'american',
        'meal_type': 'breakfast',
        'difficulty': 'easy',
        'prep': 10,
        'cook': 30,
        'servings': 6,
        'tags': ['breakfast', 'meal-prep', 'oats'],
        'instructions': (
            'Preheat oven to 350F.\n'
            'Combine dry ingredients in a bowl; combine wet in another.\n'
            'Mix together, pour into greased baking dish, bake 30 minutes.'
        ),
        'ingredients': [
            (3, 'cup', 'rolled oats', None),
            (1, 'cup', 'brown sugar', 'packed'),
            (2, 'tsp', 'baking powder', None),
            (1, 'tsp', 'salt', None),
            (1, 'cup', 'milk', None),
            (2, 'whole', 'eggs', 'beaten'),
            (0.5, 'cup', 'butter', 'melted'),
        ],
    },
    {
        'name': 'Chipotle Black Bean Soup',
        'description': 'Smoky, spicy black bean soup',
        'cuisine': 'mexican',
        'meal_type': 'dinner',
        'difficulty': 'easy',
        'prep': 10,
        'cook': 30,
        'servings': 4,
        'tags': ['vegetarian', 'soup', 'spicy', 'comfort'],
        'instructions': (
            'Sauté onion and garlic in oil until soft.\n'
            'Add beans, broth, tomatoes, and chipotle. Simmer 20 minutes.\n'
            'Blend partially, serve with lime and cilantro.'
        ),
        'ingredients': [
            (2, 'can', 'black beans', 'drained'),
            (1, 'whole', 'yellow onion', 'diced'),
            (3, 'clove', 'garlic', 'minced'),
            (2, 'tbsp', 'olive oil', None),
            (2, 'cup', 'vegetable broth', None),
            (1, 'can', 'diced tomatoes', None),
            (2, 'whole', 'chipotle peppers in adobo', 'minced'),
            (1, 'tsp', 'cumin', None),
            (None, 'to_taste', 'salt', None),
        ],
    },
    {
        'name': 'High Protein Waffles',
        'description': 'Protein-packed waffles for breakfast',
        'cuisine': 'american',
        'meal_type': 'breakfast',
        'difficulty': 'easy',
        'prep': 5,
        'cook': 15,
        'servings': 4,
        'tags': ['breakfast', 'protein', 'meal-prep'],
        'instructions': ('Whisk dry ingredients. Whisk wet. Combine.\nCook in preheated waffle iron until golden.'),
        'ingredients': [
            (1, 'cup', 'oat flour', None),
            (1, 'scoop', 'protein powder', None),
            (1, 'tsp', 'baking powder', None),
            (1, 'cup', 'milk', None),
            (2, 'whole', 'eggs', None),
            (1, 'tbsp', 'honey', None),
            (1, 'tsp', 'vanilla extract', None),
        ],
    },
    {
        'name': 'Cream Cheese Stuffed Chicken',
        'description': 'Chicken breasts stuffed with seasoned cream cheese',
        'cuisine': 'american',
        'meal_type': 'dinner',
        'difficulty': 'medium',
        'prep': 15,
        'cook': 30,
        'servings': 4,
        'tags': ['chicken', 'low-carb', 'protein'],
        'instructions': (
            'Preheat oven to 400F.\n'
            'Butterfly chicken breasts, fill with seasoned cream cheese mixture.\n'
            'Secure with toothpicks, sear both sides, then bake 20 minutes.'
        ),
        'ingredients': [
            (4, 'whole', 'chicken breasts', 'boneless skinless'),
            (8, 'oz', 'cream cheese', 'softened'),
            (2, 'clove', 'garlic', 'minced'),
            (0.25, 'cup', 'parmesan cheese', 'grated'),
            (1, 'tbsp', 'fresh chives', 'chopped'),
            (2, 'tbsp', 'olive oil', None),
            (None, 'to_taste', 'salt and pepper', None),
        ],
    },
    {
        'name': 'Homemade Tomato Sauce',
        'description': 'Simple long-simmered tomato sauce',
        'cuisine': 'italian',
        'meal_type': 'sauce',
        'difficulty': 'easy',
        'prep': 10,
        'cook': 90,
        'servings': 8,
        'tags': ['sauce', 'pantry', 'freezer-friendly'],
        'instructions': (
            'Sweat onions and garlic in olive oil over low heat.\n'
            'Add crushed tomatoes, herbs, and salt.\n'
            'Simmer uncovered 90 minutes, stirring occasionally.'
        ),
        'ingredients': [
            (2, 'can', 'crushed tomatoes', '28 oz each'),
            (1, 'whole', 'yellow onion', 'diced fine'),
            (4, 'clove', 'garlic', 'minced'),
            (0.25, 'cup', 'olive oil', None),
            (2, 'tbsp', 'fresh basil', 'chopped'),
            (1, 'tsp', 'oregano', 'dried'),
            (1, 'tsp', 'salt', None),
            (1, 'pinch', 'red pepper flakes', None),
        ],
    },
    {
        'name': "Chris' Salsa",
        'description': 'Fresh tomato-jalapeno salsa',
        'cuisine': 'mexican',
        'meal_type': 'side',
        'difficulty': 'easy',
        'prep': 10,
        'cook': 0,
        'servings': 4,
        'tags': ['salsa', 'fresh', 'no-cook'],
        'instructions': 'Dice all ingredients. Combine in a bowl, stir, rest 10 minutes.',
        'ingredients': [
            (4, 'whole', 'roma tomatoes', 'diced'),
            (1, 'whole', 'jalapeno', 'seeded and minced'),
            (0.5, 'whole', 'red onion', 'diced fine'),
            (0.25, 'cup', 'cilantro', 'chopped'),
            (1, 'whole', 'lime', 'juiced'),
            (None, 'to_taste', 'salt', None),
        ],
    },
    {
        'name': 'Cheesecake Pie',
        'description': 'Simple no-bake cheesecake pie',
        'cuisine': 'american',
        'meal_type': 'dessert',
        'difficulty': 'medium',
        'prep': 20,
        'cook': 0,
        'servings': 8,
        'tags': ['dessert', 'no-bake', 'cheesecake'],
        'instructions': (
            'Beat cream cheese, sugar, and vanilla until smooth.\n'
            'Fold in whipped topping, pour into graham crust.\n'
            'Chill at least 4 hours before serving.'
        ),
        'ingredients': [
            (16, 'oz', 'cream cheese', 'softened'),
            (0.75, 'cup', 'sugar', None),
            (1, 'tsp', 'vanilla extract', None),
            (8, 'oz', 'whipped topping', 'thawed'),
            (1, 'whole', 'graham cracker crust', None),
        ],
    },
    {
        'name': 'Crock Pot Lentil Sweet Potato Soup',
        'description': 'Hearty lentil soup with sweet potato',
        'cuisine': 'mediterranean',
        'meal_type': 'dinner',
        'difficulty': 'easy',
        'prep': 15,
        'cook': 300,
        'servings': 6,
        'tags': ['crockpot', 'vegetarian', 'soup', 'meal-prep'],
        'instructions': (
            'Add all ingredients to the slow cooker.\nCook on low 5-6 hours or high 3 hours.\nStir well before serving; adjust salt.'
        ),
        'ingredients': [
            (1.5, 'cup', 'green lentils', 'rinsed'),
            (2, 'whole', 'sweet potato', 'diced'),
            (1, 'whole', 'yellow onion', 'diced'),
            (2, 'clove', 'garlic', 'minced'),
            (6, 'cup', 'vegetable broth', None),
            (1, 'tsp', 'smoked paprika', None),
            (1, 'tsp', 'cumin', None),
            (0.5, 'tsp', 'salt', None),
        ],
    },
    {
        'name': 'Banana Bread',
        'description': 'Classic banana bread',
        'cuisine': 'american',
        'meal_type': 'dessert',
        'difficulty': 'easy',
        'prep': 15,
        'cook': 60,
        'servings': 10,
        'tags': ['bread', 'dessert', 'baking'],
        'instructions': (
            'Preheat oven to 350F. Grease loaf pan.\n'
            'Mash bananas, mix with wet ingredients.\n'
            'Fold in dry ingredients. Bake 60 minutes until toothpick clean.'
        ),
        'ingredients': [
            (3, 'whole', 'ripe bananas', 'mashed'),
            (0.5, 'cup', 'butter', 'melted'),
            (1, 'cup', 'sugar', None),
            (2, 'whole', 'eggs', None),
            (1, 'tsp', 'vanilla extract', None),
            (1.5, 'cup', 'all-purpose flour', None),
            (1, 'tsp', 'baking soda', None),
            (0.5, 'tsp', 'salt', None),
        ],
    },
]


def _ensure_lookup_seeded(session: Session) -> None:
    """Safety net: if Alembic's seed path didn't run, populate the lookup tables."""
    existing_units = {row[0] for row in session.execute(sqlalchemy.text('SELECT name FROM recipe_units')).all()}
    for unit in RECIPE_UNITS:
        if unit not in existing_units:
            session.add(RecipeUnit(name=unit))

    existing_diff = {row[0] for row in session.execute(sqlalchemy.text('SELECT name FROM recipe_difficulty')).all()}
    for d in RECIPE_DIFFICULTIES:
        if d not in existing_diff:
            session.add(RecipeDifficulty(name=d))

    existing_cuisine = {row[0] for row in session.execute(sqlalchemy.text('SELECT name FROM recipe_cuisine')).all()}
    for c in RECIPE_CUISINES:
        if c not in existing_cuisine:
            session.add(RecipeCuisine(name=c))

    existing_meal = {row[0] for row in session.execute(sqlalchemy.text('SELECT name FROM recipe_meal_type')).all()}
    for m in RECIPE_MEAL_TYPES:
        if m not in existing_meal:
            session.add(RecipeMealType(name=m))

    session.flush()


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM recipe_ingredients'))
    session.execute(sqlalchemy.text('DELETE FROM recipes'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    _ensure_lookup_seeded(session)

    recipes: list[Recipe] = []
    for rep in range(scale):
        for bp in RECIPE_BLUEPRINTS:
            name = bp['name'] if scale == 1 else f'{bp["name"]} #{rep + 1}'
            rating = random.choice([None, 3, 4, 4, 5, 5])
            times_made = random.choice([0, 0, 1, 2, 3, 5, 8])
            recipes.append(
                _recipe(
                    name=name,
                    description=bp['description'],
                    cuisine=bp['cuisine'],
                    meal_type=bp['meal_type'],
                    difficulty=bp['difficulty'],
                    prep=bp['prep'],
                    cook=bp['cook'],
                    servings=bp['servings'],
                    tags=bp['tags'],
                    instructions=bp['instructions'],
                    ingredients=bp['ingredients'],
                    rating=rating,
                    times_made=times_made,
                )
            )

    session.add_all(recipes)
    session.flush()

    cuisine_counts: dict[str, int] = {}
    for r in recipes:
        cuisine_counts[r.cuisine or 'none'] = cuisine_counts.get(r.cuisine or 'none', 0) + 1
    details = ', '.join(f'{v} {k}' for k, v in sorted(cuisine_counts.items()))

    return SeedResult(model='Recipe', count=len(recipes), details=details)
