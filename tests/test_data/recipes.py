from ichrisbirch.models import Recipe
from ichrisbirch.models import RecipeIngredient

# Lookup tables (units, cuisines, meal types, difficulties) are populated by the
# initial migration — no need to insert them here.

BASE_DATA: list[Recipe] = [
    Recipe(
        name='Test Pasta',
        description='A simple test pasta',
        cuisine='italian',
        meal_type='dinner',
        difficulty='easy',
        prep_time_minutes=10,
        cook_time_minutes=15,
        total_time_minutes=25,
        servings=4,
        tags=['pasta', 'quick', 'weeknight'],
        instructions='Boil pasta. Add sauce. Serve.',
        rating=4,
        times_made=3,
        ingredients=[
            RecipeIngredient(position=0, quantity=1, unit='lb', item='spaghetti'),
            RecipeIngredient(position=1, quantity=2, unit='cup', item='tomato sauce'),
            RecipeIngredient(position=2, quantity=0.25, unit='cup', item='parmesan', prep_note='grated'),
            RecipeIngredient(position=3, quantity=2, unit='clove', item='garlic', prep_note='minced'),
        ],
    ),
    Recipe(
        name='Test Salad',
        description='A fresh test salad',
        cuisine='mediterranean',
        meal_type='lunch',
        difficulty='easy',
        prep_time_minutes=15,
        cook_time_minutes=0,
        total_time_minutes=15,
        servings=2,
        tags=['salad', 'fresh', 'no-cook'],
        instructions='Chop everything. Toss with dressing.',
        rating=5,
        times_made=1,
        ingredients=[
            RecipeIngredient(position=0, quantity=1, unit='whole', item='romaine lettuce', prep_note='chopped'),
            RecipeIngredient(position=1, quantity=0.5, unit='cup', item='cherry tomatoes', prep_note='halved'),
            RecipeIngredient(position=2, quantity=2, unit='tbsp', item='olive oil'),
            RecipeIngredient(position=3, quantity=1, unit='tbsp', item='lemon juice'),
        ],
    ),
    Recipe(
        name='Test Dessert',
        description='A sweet test dessert',
        cuisine='french',
        meal_type='dessert',
        difficulty='medium',
        prep_time_minutes=30,
        cook_time_minutes=45,
        total_time_minutes=75,
        servings=8,
        tags=['dessert', 'baking', 'special'],
        instructions='Bake until golden.',
        rating=3,
        times_made=0,
        ingredients=[
            RecipeIngredient(position=0, quantity=2, unit='cup', item='flour'),
            RecipeIngredient(position=1, quantity=1, unit='cup', item='sugar'),
            RecipeIngredient(position=2, quantity=0.5, unit='cup', item='butter', prep_note='softened'),
            RecipeIngredient(position=3, quantity=3, unit='whole', item='eggs'),
        ],
    ),
]
