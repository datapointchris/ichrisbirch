import pytest
from fastapi import status

import tests.util
from ichrisbirch.models.box import BoxSize
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('boxes')
    yield
    delete_test_data('boxes')


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/box-packing/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing')


def test_index_with_box_id(test_app_logged_in, test_api_logged_in):
    """Test viewing a specific box."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    response = test_app_logged_in.get(f'/box-packing/{first_box_id}/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing')


def test_edit_page(test_app_logged_in, test_api_logged_in):
    """Test edit page loads."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    response = test_app_logged_in.get(f'/box-packing/edit/{first_box_id}/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Edit Box')


def test_all_boxes(test_app_logged_in):
    response = test_app_logged_in.get('/box-packing/all/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing')


def test_orphans(test_app_logged_in):
    response = test_app_logged_in.get('/box-packing/orphans/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing - Search')


def test_search_page(test_app_logged_in):
    response = test_app_logged_in.get('/box-packing/search/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing - Search')


def test_search_post(test_app_logged_in):
    response = test_app_logged_in.post('/box-packing/search/', data={'search_text': 'find'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Box Packing - Search')


def test_crud_add_box(test_app_logged_in):
    """Test adding a new box."""
    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'add_box',
            'box_name': 'Test Box',
            'box_number': 99,
            'box_size': BoxSize.Medium.value,
            'essential': '1',
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert 'Test Box' in response.data.decode('utf-8') or 'created' in response.data.decode('utf-8').lower()


def test_crud_edit_box(test_app_logged_in, test_api_logged_in):
    """Test editing a box - critical test since we changed the API contract."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box = boxes.json()[0]
    box_id = first_box['id']

    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'edit_box',
            'box_id': box_id,
            'box_name': 'Updated Box Name',
            'box_number': first_box['number'],
            'box_size': first_box['size'],
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify the box was actually updated
    updated_box = test_api_logged_in.get(f'/box-packing/boxes/{box_id}/')
    assert updated_box.json()['name'] == 'Updated Box Name'


def test_crud_delete_box(test_app_logged_in, test_api_logged_in):
    """Test deleting a box."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    box_to_delete = boxes.json()[-1]  # Delete last box
    box_id = box_to_delete['id']

    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'delete_box',
            'box_id': box_id,
            'box_number': box_to_delete['number'],
            'box_name': box_to_delete['name'],
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify the box was deleted
    deleted_box = test_api_logged_in.get(f'/box-packing/boxes/{box_id}/')
    assert deleted_box.status_code == status.HTTP_404_NOT_FOUND


def test_crud_add_item(test_app_logged_in, test_api_logged_in):
    """Test adding an item to a box."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box = boxes.json()[0]
    box_id = first_box['id']

    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'add_item',
            'box_id': box_id,
            'box_number': first_box['number'],
            'box_name': first_box['name'],
            'item_name': 'New Test Item',
            'essential': '1',
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_orphan_item(test_app_logged_in, test_api_logged_in):
    """Test orphaning an item - critical test since we changed the API contract."""
    # Get a box with items
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    box_with_items = None
    for box in boxes.json():
        if box['items']:
            box_with_items = box
            break

    assert box_with_items is not None, 'Need a box with items for this test'
    item = box_with_items['items'][0]
    item_id = item['id']

    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'orphan_item',
            'item_id': item_id,
            'item_name': item['name'],
            'box_id': box_with_items['id'],
            'box_number': box_with_items['number'],
            'box_name': box_with_items['name'],
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify the item is now orphaned
    orphans = test_api_logged_in.get('/box-packing/items/orphans/')
    orphan_ids = [o['id'] for o in orphans.json()]
    assert item_id in orphan_ids


def test_crud_add_orphan_to_box(test_app_logged_in, test_api_logged_in):
    """Test adding an orphan item back to a box - critical test since we changed the API contract."""
    # First create an orphan by orphaning an item
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    box_with_items = None
    for box in boxes.json():
        if box['items']:
            box_with_items = box
            break

    assert box_with_items is not None, 'Need a box with items for this test'
    item = box_with_items['items'][0]
    item_id = item['id']

    # Orphan the item first
    test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'orphan_item',
            'item_id': item_id,
            'item_name': item['name'],
            'box_id': box_with_items['id'],
            'box_number': box_with_items['number'],
            'box_name': box_with_items['name'],
        },
        follow_redirects=True,
    )

    # Verify it's orphaned
    orphans = test_api_logged_in.get('/box-packing/items/orphans/')
    assert item_id in [o['id'] for o in orphans.json()]

    # Now add the orphan back to a box
    target_box = boxes.json()[0]
    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'add_orphan_to_box',
            'item_id': item_id,
            'item_name': item['name'],
            'box_id': target_box['id'],
            'box_number': target_box['number'],
            'box_name': target_box['name'],
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify the item is no longer orphaned
    orphans_after = test_api_logged_in.get('/box-packing/items/orphans/')
    assert item_id not in [o['id'] for o in orphans_after.json()]


def test_crud_delete_item(test_app_logged_in, test_api_logged_in):
    """Test deleting an item from a box."""
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    box_with_items = None
    for box in boxes.json():
        if box['items']:
            box_with_items = box
            break

    assert box_with_items is not None, 'Need a box with items for this test'
    item = box_with_items['items'][0]
    item_id = item['id']

    response = test_app_logged_in.post(
        '/box-packing/crud/',
        data={
            'action': 'delete_item',
            'item_id': item_id,
            'item_name': item['name'],
            'box_id': box_with_items['id'],
            'box_number': box_with_items['number'],
            'box_name': box_with_items['name'],
        },
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify the item was deleted
    deleted_item = test_api_logged_in.get(f'/box-packing/items/{item_id}/')
    assert deleted_item.status_code == status.HTTP_404_NOT_FOUND
