import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/recipes/'
NEW_OBJ = schemas.RecipeCreate(
    name='Margherita Pizza',
    description='Classic Neapolitan',
    cuisine='italian',
    meal_type='dinner',
    difficulty='medium',
    prep_time_minutes=20,
    cook_time_minutes=10,
    total_time_minutes=30,
    servings=2,
    tags=['pizza', 'italian', 'classic'],
    instructions='Make dough. Top with tomato, mozzarella, basil. Bake hot.',
    rating=5,
    ingredients=[
        schemas.RecipeIngredientCreate(position=0, quantity=250, unit='g', item='00 flour'),
        schemas.RecipeIngredientCreate(position=1, quantity=175, unit='ml', item='water'),
        schemas.RecipeIngredientCreate(position=2, quantity=5, unit='g', item='salt'),
        schemas.RecipeIngredientCreate(position=3, quantity=125, unit='g', item='fresh mozzarella'),
        schemas.RecipeIngredientCreate(position=4, quantity=None, unit='to_taste', item='fresh basil'),
    ],
)


@pytest.fixture
def recipe_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'recipes')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='name')
    return client, crud_tester


def test_read_one(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    crud_tester.test_read_many(client)


def test_create(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    crud_tester.test_create(client)


def test_delete(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    crud_tester.test_lifecycle(client)


def test_create_persists_ingredients(recipe_crud_tester):
    """POST /recipes/ with nested ingredients should round-trip fully."""
    client, _ = recipe_crud_tester
    created = client.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    data = created.json()
    assert len(data['ingredients']) == 5
    # Ingredients come back sorted by position
    assert [ing['item'] for ing in data['ingredients']] == ['00 flour', 'water', 'salt', 'fresh mozzarella', 'fresh basil']
    assert data['ingredients'][4]['unit'] == 'to_taste'
    assert data['ingredients'][4]['quantity'] is None


def test_read_one_includes_ingredients(recipe_crud_tester):
    client, crud_tester = recipe_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.get(f'{ENDPOINT}{first_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert len(data['ingredients']) > 0
    for ing in data['ingredients']:
        assert 'item' in ing
        assert 'position' in ing


def test_list_filter_by_cuisine(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(ENDPOINT, params={'cuisine': 'italian'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]['name'] == 'Test Pasta'


def test_list_filter_by_meal_type(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(ENDPOINT, params={'meal_type': 'dessert'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]['name'] == 'Test Dessert'


def test_list_filter_by_rating_min(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(ENDPOINT, params={'rating_min': 4})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    recipes = response.json()
    names = {r['name'] for r in recipes}
    # Test Pasta (4) and Test Salad (5) qualify; Test Dessert (3) does not
    assert names == {'Test Pasta', 'Test Salad'}


def test_list_filter_by_max_total_time(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(ENDPOINT, params={'max_total_time': 30})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    names = {r['name'] for r in response.json()}
    # Pasta (25 min) and Salad (15 min) are <= 30; Dessert (75) is not
    assert names == {'Test Pasta', 'Test Salad'}


def test_search_by_name(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'pasta'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Pasta'


def test_search_by_tag(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'fresh'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    # 'fresh' appears in Test Salad's tags
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Salad'


def test_search_by_instructions(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'golden'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    # 'golden' appears in Test Dessert's instructions ('Bake until golden.')
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Dessert'


def test_search_empty_query_returns_empty(recipe_crud_tester):
    client, _ = recipe_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': '   '})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() == []


class TestSearchByIngredients:
    def test_any_match_ranks_by_coverage(self, recipe_crud_tester):
        """match=any: Test Pasta uses garlic and tomato sauce — 2 hits; Test Salad uses tomato — 1 hit."""
        client, _ = recipe_crud_tester
        response = client.get(
            f'{ENDPOINT}search-by-ingredients/',
            params={'have': 'garlic,tomato', 'match': 'any'},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        results = response.json()
        # Pasta (garlic + tomato sauce) ranked above Salad (cherry tomatoes only)
        assert results[0]['recipe']['name'] == 'Test Pasta'
        assert results[0]['coverage'] == 2
        assert results[1]['recipe']['name'] == 'Test Salad'
        assert results[1]['coverage'] == 1

    def test_all_match_filters_strict(self, recipe_crud_tester):
        """match=all: only recipes containing every listed ingredient."""
        client, _ = recipe_crud_tester
        response = client.get(
            f'{ENDPOINT}search-by-ingredients/',
            params={'have': 'garlic,tomato', 'match': 'all'},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        results = response.json()
        assert len(results) == 1
        assert results[0]['recipe']['name'] == 'Test Pasta'

    def test_total_ingredients_reported(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.get(
            f'{ENDPOINT}search-by-ingredients/',
            params={'have': 'flour', 'match': 'any'},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        results = response.json()
        assert len(results) == 1
        assert results[0]['recipe']['name'] == 'Test Dessert'
        assert results[0]['total_ingredients'] == 4

    def test_empty_have_returns_empty(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.get(f'{ENDPOINT}search-by-ingredients/', params={'have': ''})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []


class TestServingScaling:
    def test_no_scaling_param_returns_base(self, recipe_crud_tester):
        client, crud_tester = recipe_crud_tester
        first_id = crud_tester.item_id_by_position(client, position=1)
        response = client.get(f'{ENDPOINT}{first_id}/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        for ing in response.json()['ingredients']:
            assert ing['scaled_quantity'] is None

    def test_scaling_doubles_quantities(self, recipe_crud_tester):
        """Test Pasta servings=4; request servings=8 → all quantities doubled."""
        client, _ = recipe_crud_tester
        all_recipes = client.get(ENDPOINT).json()
        pasta = next(r for r in all_recipes if r['name'] == 'Test Pasta')
        response = client.get(f'{ENDPOINT}{pasta["id"]}/', params={'servings': 8})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        # All base quantities should double
        by_item = {ing['item']: ing for ing in data['ingredients']}
        assert by_item['spaghetti']['scaled_quantity'] == 2.0
        assert by_item['tomato sauce']['scaled_quantity'] == 4.0
        assert by_item['parmesan']['scaled_quantity'] == 0.5
        assert by_item['garlic']['scaled_quantity'] == 4.0

    def test_scaling_halves_quantities(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        all_recipes = client.get(ENDPOINT).json()
        pasta = next(r for r in all_recipes if r['name'] == 'Test Pasta')
        response = client.get(f'{ENDPOINT}{pasta["id"]}/', params={'servings': 2})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        by_item = {ing['item']: ing for ing in response.json()['ingredients']}
        assert by_item['spaghetti']['scaled_quantity'] == 0.5
        assert by_item['tomato sauce']['scaled_quantity'] == 1.0


class TestMarkMade:
    def test_mark_made_increments_count(self, recipe_crud_tester):
        client, crud_tester = recipe_crud_tester
        first_id = crud_tester.item_id_by_position(client, position=1)
        before = client.get(f'{ENDPOINT}{first_id}/').json()
        before_count = before['times_made']

        response = client.post(f'{ENDPOINT}{first_id}/mark-made/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['times_made'] == before_count + 1
        assert data['last_made_date'] is not None

    def test_mark_made_from_zero(self, recipe_crud_tester):
        """Test Dessert starts with times_made=0."""
        client, _ = recipe_crud_tester
        all_recipes = client.get(ENDPOINT).json()
        dessert = next(r for r in all_recipes if r['name'] == 'Test Dessert')
        assert dessert['times_made'] == 0
        response = client.post(f'{ENDPOINT}{dessert["id"]}/mark-made/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['times_made'] == 1

    def test_mark_made_not_found(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.post(f'{ENDPOINT}99999/mark-made/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestUpdateRecipe:
    def test_update_simple_fields(self, recipe_crud_tester):
        client, crud_tester = recipe_crud_tester
        first_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(
            f'{ENDPOINT}{first_id}/',
            json={'rating': 5, 'notes': 'Amazing!', 'tags': ['updated', 'favorite']},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['rating'] == 5
        assert data['notes'] == 'Amazing!'
        assert data['tags'] == ['updated', 'favorite']

    def test_update_ingredients_replace_all(self, recipe_crud_tester):
        client, crud_tester = recipe_crud_tester
        first_id = crud_tester.item_id_by_position(client, position=1)
        new_ingredients = [
            {'position': 0, 'quantity': 100, 'unit': 'g', 'item': 'new ingredient 1'},
            {'position': 1, 'quantity': 200, 'unit': 'g', 'item': 'new ingredient 2'},
        ]
        response = client.patch(
            f'{ENDPOINT}{first_id}/',
            json={'ingredients': new_ingredients},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert len(data['ingredients']) == 2
        assert [ing['item'] for ing in data['ingredients']] == ['new ingredient 1', 'new ingredient 2']

    def test_update_not_found(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'rating': 5})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestStats:
    def test_stats_returns_expected_shape(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.get(f'{ENDPOINT}stats/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['total_recipes'] == 3
        # Pasta=3 + Salad=1 + Dessert=0 = 4
        assert data['total_times_cooked'] == 4
        assert data['average_rating'] == 4.0  # (4 + 5 + 3) / 3
        assert data['unique_cuisines'] == 3  # italian, mediterranean, french
        assert len(data['rating_breakdown']) == 3
        assert len(data['cuisine_breakdown']) == 3
        # Most-made: Pasta (3x) is the only recipe with > 0 qualifying in top
        most_made_names = [r['name'] for r in data['most_made']]
        assert most_made_names[0] == 'Test Pasta'
        # Untried: Test Dessert has times_made=0
        untried_names = [r['name'] for r in data['untried']]
        assert 'Test Dessert' in untried_names


class TestAISuggest:
    @patch('ichrisbirch.api.endpoints.recipes.AnthropicAssistant')
    def test_ai_suggest_parses_candidates(self, mock_assistant_cls, recipe_crud_tester):
        """Mock Claude's response and verify the endpoint parses/validates candidates correctly."""
        client, _ = recipe_crud_tester

        fake_candidates = {
            'candidates': [
                {
                    'name': 'Quick Chicken Stir Fry',
                    'description': 'A fast weeknight stir fry',
                    'source_url': 'https://example.com/stir-fry',
                    'source_name': 'Example Recipes',
                    'prep_time_minutes': 10,
                    'cook_time_minutes': 8,
                    'total_time_minutes': 18,
                    'servings': 2,
                    'difficulty': 'easy',
                    'cuisine': 'asian',
                    'meal_type': 'dinner',
                    'tags': ['quick', 'stir-fry'],
                    'instructions': 'Heat wok. Stir fry chicken, then veg, add sauce.',
                    'ingredients': [
                        {
                            'position': 0,
                            'quantity': 1,
                            'unit': 'lb',
                            'item': 'chicken breast',
                            'prep_note': 'sliced',
                            'is_optional': False,
                            'ingredient_group': None,
                        },
                        {
                            'position': 1,
                            'quantity': 2,
                            'unit': 'tbsp',
                            'item': 'soy sauce',
                            'prep_note': None,
                            'is_optional': False,
                            'ingredient_group': None,
                        },
                    ],
                }
            ]
        }

        mock_assistant = MagicMock()
        mock_assistant.generate.return_value = json.dumps(fake_candidates)
        mock_assistant_cls.return_value = mock_assistant
        # The endpoint calls AnthropicAssistant.parse_json (staticmethod) on the CLASS,
        # so the mock class must delegate to the real staticmethod or parsing silently fails.
        mock_assistant_cls.parse_json = AnthropicAssistant.parse_json

        response = client.post(
            f'{ENDPOINT}ai-suggest/',
            json={'have': ['chicken', 'soy sauce'], 'want': 'quick dinner', 'count': 1},
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert len(data['candidates']) == 1
        candidate = data['candidates'][0]
        assert candidate['name'] == 'Quick Chicken Stir Fry'
        assert candidate['source_url'] == 'https://example.com/stir-fry'
        assert len(candidate['ingredients']) == 2

        # Verify web_search tool was passed and the AnthropicAssistant was instantiated
        mock_assistant_cls.assert_called_once()
        call_kwargs = mock_assistant_cls.call_args.kwargs
        tools = call_kwargs.get('tools')
        assert tools is not None
        assert any(t.get('name') == 'web_search' for t in tools)

    def test_ai_save_persists_candidate(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        candidate = {
            'name': 'Saved AI Recipe',
            'description': 'Saved from AI',
            'source_url': 'https://example.com/saved',
            'source_name': 'Example',
            'prep_time_minutes': 5,
            'cook_time_minutes': 10,
            'total_time_minutes': 15,
            'servings': 1,
            'difficulty': 'easy',
            'cuisine': 'other',
            'meal_type': 'snack',
            'tags': ['ai', 'quick'],
            'instructions': 'Do thing.',
            'ingredients': [
                {
                    'position': 0,
                    'quantity': 1,
                    'unit': 'piece',
                    'item': 'apple',
                    'prep_note': None,
                    'is_optional': False,
                    'ingredient_group': None,
                },
            ],
        }
        response = client.post(f'{ENDPOINT}ai-save/', json=candidate)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        saved = response.json()
        assert saved['name'] == 'Saved AI Recipe'
        assert saved['source_url'] == 'https://example.com/saved'
        assert len(saved['ingredients']) == 1
        assert saved['ingredients'][0]['item'] == 'apple'


class TestRecipesNotFound:
    def test_read_one_not_found(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, recipe_crud_tester):
        client, _ = recipe_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
