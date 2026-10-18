import datetime as dt
from urllib.parse import quote

import pytest
from fastapi import status

from ichrisbirch import models
from ichrisbirch.api.endpoints.shopping import PURCHASES_SHOWN
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

SECTIONS = '/shopping/sections'
ITEMS = '/shopping/items'
PURCHASES = '/shopping/purchases'


@pytest.fixture
def seeded(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'shopping_sections')
    return client, session


@pytest.fixture
def client(seeded):
    return seeded[0]


def ok(response, code=status.HTTP_200_OK):
    assert response.status_code == code, show_status_and_response(response)
    return None if code == status.HTTP_204_NO_CONTENT else response.json()


def refused(response, code):
    assert response.status_code == code, show_status_and_response(response)
    return response.json()['message']


def names(rows) -> list[str]:
    return [row['name'] for row in rows]


def item(client, name: str) -> dict:
    return ok(client.get(f'{ITEMS}/{name}'))


def listed(client) -> list[tuple[str | None, str]]:
    """The list as a person reads it: (section, item) in order."""
    return [(row['section_name'], row['name']) for row in ok(client.get(ITEMS))]


def add(client, name: str, code=status.HTTP_201_CREATED, **fields) -> dict:
    return ok(client.post(ITEMS, json={'name': name, **fields}), code)


def check_off(client, name: str) -> dict:
    return ok(client.post(f'{ITEMS}/{name}/purchases'), status.HTTP_201_CREATED)


def escaped(name: str) -> str:
    """A name as the CLI puts it in a path, every slash escaped, as Go's `url.PathEscape` does."""
    return quote(name, safe='')


class TestSections:
    def test_sections_read_in_rank_order(self, client):
        assert names(ok(client.get(SECTIONS))) == ['Costco', 'Grocery', 'Hardware']

    def test_a_new_section_goes_last(self, client):
        ok(client.post(SECTIONS, json={'name': 'Online'}), status.HTTP_201_CREATED)
        assert names(ok(client.get(SECTIONS)))[-1] == 'Online'

    def test_a_name_is_taken_without_regard_to_case(self, client):
        detail = refused(client.post(SECTIONS, json={'name': 'costco'}), status.HTTP_409_CONFLICT)
        assert 'Costco' in detail

    def test_a_blank_name_is_refused(self, client):
        refused(client.post(SECTIONS, json={'name': '   '}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_rename_by_name(self, client):
        renamed = ok(client.patch(f'{SECTIONS}/grocery', json={'name': 'Safeway'}))
        assert renamed['name'] == 'Safeway'
        assert ('Safeway', 'bananas') in listed(client)

    def test_rename_onto_another_section_is_refused(self, client):
        refused(client.patch(f'{SECTIONS}/Grocery', json={'name': 'COSTCO'}), status.HTTP_409_CONFLICT)

    def test_a_section_may_change_only_its_case(self, client):
        assert ok(client.patch(f'{SECTIONS}/Costco', json={'name': 'COSTCO'}))['name'] == 'COSTCO'

    def test_a_null_name_is_refused(self, client):
        refused(client.patch(f'{SECTIONS}/Costco', json={'name': None}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_deleting_a_section_moves_its_items_to_unsorted(self, client):
        ok(client.delete(f'{SECTIONS}/Costco'), status.HTTP_204_NO_CONTENT)
        assert item(client, 'eggs')['section_id'] is None
        assert item(client, 'coffee beans')['section_id'] is None, 'an item off the list falls to Unsorted too'

    def test_a_section_moves_before_another(self, client):
        ok(client.post(f'{SECTIONS}/Hardware/rank', json={'before': 'Costco'}))
        assert names(ok(client.get(SECTIONS))) == ['Hardware', 'Costco', 'Grocery']

    def test_a_section_moves_after_another(self, client):
        ok(client.post(f'{SECTIONS}/Costco/rank', json={'after': 'Grocery'}))
        assert names(ok(client.get(SECTIONS))) == ['Grocery', 'Costco', 'Hardware']

    def test_a_section_is_not_placed_beside_itself(self, client):
        refused(client.post(f'{SECTIONS}/Costco/rank', json={'after': 'Costco'}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_a_move_names_exactly_one_neighbor(self, client):
        refused(client.post(f'{SECTIONS}/Costco/rank', json={}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_an_unknown_section_names_the_nearest(self, client):
        detail = refused(client.patch(f'{SECTIONS}/Costko', json={'name': 'x'}), status.HTTP_404_NOT_FOUND)
        assert 'Costco' in detail


class TestNamesHoldingASlash:
    def test_the_cli_moves_renames_and_deletes_a_fruit_veg_aisle_by_name(self, client):
        ok(client.post(SECTIONS, json={'name': 'Fruit/Veg'}), status.HTTP_201_CREATED)
        ok(client.post(f'{SECTIONS}/{escaped("Fruit/Veg")}/rank', json={'before': 'Costco'}))
        assert names(ok(client.get(SECTIONS)))[0] == 'Fruit/Veg'
        ok(client.patch(f'{SECTIONS}/{escaped("Fruit/Veg")}', json={'name': 'Deli/Bakery'}))
        ok(client.delete(f'{SECTIONS}/{escaped("Deli/Bakery")}'), status.HTTP_204_NO_CONTENT)
        assert names(ok(client.get(SECTIONS))) == ['Costco', 'Grocery', 'Hardware']

    def test_the_cli_moves_edits_checks_off_and_deletes_a_salt_pepper_item_by_name(self, client):
        add(client, 'salt/pepper', section='Grocery')
        ok(client.post(f'{ITEMS}/{escaped("salt/pepper")}/rank', json={'section': 'Costco'}))
        ok(client.patch(f'{ITEMS}/{escaped("salt/pepper")}', json={'note': 'the grinder'}))
        assert item(client, escaped('salt/pepper'))['section_name'] == 'Costco'
        assert check_off(client, escaped('salt/pepper'))['note'] == 'the grinder'
        ok(client.delete(f'{ITEMS}/{escaped("salt/pepper")}'), status.HTTP_204_NO_CONTENT)
        assert 'salt/pepper' not in names(ok(client.get(ITEMS, params={'status': 'all'})))


class TestReadingTheList:
    def test_the_list_is_what_is_needed_section_by_section(self, client):
        assert listed(client) == [('Costco', 'eggs'), ('Costco', 'paper towels'), ('Grocery', 'bananas')]

    def test_unsorted_reads_first(self, client):
        add(client, 'hot plate')
        assert listed(client)[0] == (None, 'hot plate')

    def test_stocked_is_what_is_off_the_list(self, client):
        assert names(ok(client.get(ITEMS, params={'status': 'stocked'}))) == ['coffee beans', 'milk']

    def test_all_is_the_whole_catalog(self, client):
        assert len(ok(client.get(ITEMS, params={'status': 'all'}))) == 5

    def test_an_unknown_status_is_refused_by_name(self, client):
        detail = refused(client.get(ITEMS, params={'status': 'bought'}), status.HTTP_422_UNPROCESSABLE_CONTENT)
        assert 'needed' in detail

    def test_one_section_by_name(self, client):
        assert names(ok(client.get(ITEMS, params={'section': 'grocery', 'status': 'all'}))) == ['bananas', 'milk']

    def test_q_puts_names_starting_with_it_first(self, client):
        add(client, 'oat milk')
        rows = ok(client.get(ITEMS, params={'q': 'MILK', 'status': 'all'}))
        assert names(rows) == ['milk', 'oat milk']

    def test_q_treats_a_wildcard_as_a_character(self, client):
        assert ok(client.get(ITEMS, params={'q': '%', 'status': 'all'})) == []

    def test_an_item_carries_its_purchase_history(self, client):
        before = item(client, 'eggs')
        assert (before['purchase_count'], before['last_purchased_ts']) == (0, None)
        check_off(client, 'eggs')
        after = item(client, 'eggs')
        assert after['purchase_count'] == 1
        assert after['last_purchased_ts'] is not None


class TestAddingByName:
    def test_a_new_name_lands_in_unsorted_on_the_list(self, client):
        created = add(client, 'wood glue')
        assert (created['section_id'], created['is_needed']) == (None, True)
        assert created['needed_ts'] is not None

    def test_a_new_name_goes_last_in_its_section(self, client):
        add(client, 'yogurt', section='Grocery')
        assert listed(client)[-1] == ('Grocery', 'yogurt')

    def test_a_known_name_returns_to_its_section_and_place(self, client):
        """Milk kept rank 4 while it was off the list, so it returns after bananas, where it sat."""
        relisted = add(client, 'Milk', code=status.HTTP_200_OK)
        assert relisted['name'] == 'milk', 'the catalog keeps the spelling it has'
        assert listed(client) == [('Costco', 'eggs'), ('Costco', 'paper towels'), ('Grocery', 'bananas'), ('Grocery', 'milk')]
        assert relisted['rank'] == 4.0

    def test_a_known_name_given_a_section_goes_there_last(self, client):
        add(client, 'milk', code=status.HTTP_200_OK, section='Costco')
        assert listed(client)[2] == ('Costco', 'milk')

    def test_a_known_name_given_a_null_section_goes_to_unsorted(self, client):
        assert add(client, 'milk', code=status.HTTP_200_OK, section=None)['section_id'] is None

    def test_a_note_on_a_listed_item_is_added_to_its_note(self, client):
        add(client, 'eggs', code=status.HTTP_200_OK, note='1 dozen · Quiche')
        assert item(client, 'eggs')['note'] == '2 dozen; 1 dozen · Quiche'

    def test_the_same_note_is_added_once(self, client):
        add(client, 'eggs', code=status.HTTP_200_OK, note='2 dozen')
        assert item(client, 'eggs')['note'] == '2 dozen'

    def test_adding_a_listed_item_creates_no_second_row(self, client):
        add(client, 'EGGS', code=status.HTTP_200_OK)
        assert names(ok(client.get(ITEMS))).count('eggs') == 1

    def test_an_unknown_section_is_refused(self, client):
        refused(client.post(ITEMS, json={'name': 'nails', 'section': 'Hardwar'}), status.HTTP_404_NOT_FOUND)


class TestEditing:
    def test_rename(self, client):
        ok(client.patch(f'{ITEMS}/eggs', json={'name': 'large eggs'}))
        assert ('Costco', 'large eggs') in listed(client)

    def test_rename_onto_a_catalog_name_is_refused(self, client):
        detail = refused(client.patch(f'{ITEMS}/eggs', json={'name': 'MILK'}), status.HTTP_409_CONFLICT)
        assert 'milk' in detail

    def test_a_null_name_is_refused(self, client):
        refused(client.patch(f'{ITEMS}/eggs', json={'name': None}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_a_blank_note_clears_it(self, client):
        assert ok(client.patch(f'{ITEMS}/eggs', json={'note': ''}))['note'] is None

    def test_a_null_section_is_unsorted(self, client):
        assert ok(client.patch(f'{ITEMS}/eggs', json={'section': None}))['section_id'] is None

    def test_taking_an_item_off_the_list_records_no_purchase(self, client):
        ok(client.patch(f'{ITEMS}/eggs', json={'is_needed': False}))
        assert 'eggs' not in names(ok(client.get(ITEMS)))
        assert item(client, 'eggs')['purchase_count'] == 0

    def test_deleting_an_item_keeps_its_purchases_under_the_name(self, client):
        check_off(client, 'eggs')
        ok(client.delete(f'{ITEMS}/eggs'), status.HTTP_204_NO_CONTENT)
        refused(client.get(f'{ITEMS}/eggs'), status.HTTP_404_NOT_FOUND)
        purchase = ok(client.get(PURCHASES))[0]
        assert (purchase['item_name'], purchase['item_id']) == ('eggs', None)


class TestMoving:
    def test_after_a_neighbor_in_another_section(self, client):
        moved = ok(client.post(f'{ITEMS}/eggs/rank', json={'section': 'Grocery', 'after': 'bananas'}))
        assert moved['section_name'] == 'Grocery'
        assert listed(client) == [('Costco', 'paper towels'), ('Grocery', 'bananas'), ('Grocery', 'eggs')]

    def test_before_a_neighbor(self, client):
        ok(client.post(f'{ITEMS}/paper towels/rank', json={'section': 'Costco', 'before': 'eggs'}))
        assert listed(client)[:2] == [('Costco', 'paper towels'), ('Costco', 'eggs')]

    def test_into_an_empty_section(self, client):
        ok(client.post(f'{ITEMS}/eggs/rank', json={'section': 'Hardware'}))
        assert listed(client)[-1] == ('Hardware', 'eggs')

    def test_into_unsorted(self, client):
        ok(client.post(f'{ITEMS}/bananas/rank', json={'section': None}))
        assert listed(client)[0] == (None, 'bananas')

    def test_a_neighbor_in_another_section_is_refused(self, client):
        detail = refused(
            client.post(f'{ITEMS}/eggs/rank', json={'section': 'Hardware', 'after': 'bananas'}), status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        assert 'Grocery' in detail

    def test_an_item_is_not_placed_beside_itself(self, client):
        refused(client.post(f'{ITEMS}/eggs/rank', json={'section': 'Costco', 'after': 'eggs'}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_a_move_names_the_section_it_lands_in(self, client):
        refused(client.post(f'{ITEMS}/eggs/rank', json={'after': 'paper towels'}), status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_a_spent_gap_renumbers_and_keeps_the_order(self, seeded):
        client, session = seeded
        eggs = session.query(models.ShoppingItem).filter_by(name='eggs').one()
        bananas = session.query(models.ShoppingItem).filter_by(name='bananas').one()
        bananas.rank = eggs.rank + 1e-7
        session.flush()
        ok(client.post(f'{ITEMS}/paper towels/rank', json={'section': 'Costco', 'after': 'eggs'}))
        assert listed(client) == [('Costco', 'eggs'), ('Costco', 'paper towels'), ('Grocery', 'bananas')]


class TestCheckingOff:
    def test_a_purchase_takes_the_item_off_the_list(self, client):
        purchase = check_off(client, 'eggs')
        assert (purchase['item_name'], purchase['section_name'], purchase['note']) == ('eggs', 'Costco', '2 dozen')
        assert 'eggs' not in names(ok(client.get(ITEMS)))

    def test_the_purchase_takes_the_note_from_the_item(self, client):
        check_off(client, 'eggs')
        assert item(client, 'eggs')['note'] is None

    def test_an_item_off_the_list_is_not_checked_off(self, client):
        detail = refused(client.post(f'{ITEMS}/milk/purchases'), status.HTTP_409_CONFLICT)
        assert 'not on the list' in detail

    def test_undo_puts_the_item_back_with_its_note(self, client):
        purchase = check_off(client, 'eggs')
        ok(client.delete(f'{PURCHASES}/{purchase["id"]}'), status.HTTP_204_NO_CONTENT)
        restored = item(client, 'eggs')
        assert (restored['is_needed'], restored['note'], restored['purchase_count']) == (True, '2 dozen', 0)

    def test_undo_leaves_an_item_listed_again_alone(self, client):
        purchase = check_off(client, 'eggs')
        add(client, 'eggs', code=status.HTTP_200_OK, note='6')
        ok(client.delete(f'{PURCHASES}/{purchase["id"]}'), status.HTTP_204_NO_CONTENT)
        assert item(client, 'eggs')['note'] == '6'

    def test_undoing_an_unknown_purchase_is_a_404(self, client):
        refused(client.delete(f'{PURCHASES}/01900000-0000-7000-8000-000000000000'), status.HTTP_404_NOT_FOUND)


class TestPurchaseLog:
    def test_newest_first(self, client):
        check_off(client, 'eggs')
        check_off(client, 'bananas')
        assert [row['item_name'] for row in ok(client.get(PURCHASES))] == ['bananas', 'eggs']

    def test_an_absent_limit_takes_the_newest_of_the_log(self, seeded):
        client, session = seeded
        start = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        session.add_all(
            models.ShoppingPurchase(item_name=f'thing {n}', purchased_ts=start + dt.timedelta(minutes=n))
            for n in range(PURCHASES_SHOWN + 1)
        )
        session.flush()
        read = ok(client.get(PURCHASES))
        assert (len(read), read[0]['item_name']) == (PURCHASES_SHOWN, f'thing {PURCHASES_SHOWN}')

    @pytest.mark.parametrize(('limit', 'count'), [(1, 1), (0, 0)])
    def test_a_limit_caps_the_log(self, seeded, limit, count):
        client, session = seeded
        insert_test_data_transactional(session, 'shopping_purchases')
        assert len(ok(client.get(PURCHASES, params={'limit': limit}))) == count

    def test_a_negative_limit_is_a_422(self, client):
        refused(client.get(PURCHASES, params={'limit': -1}), status.HTTP_422_UNPROCESSABLE_CONTENT)
