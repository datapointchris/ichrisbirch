import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.box import BoxSize
from tests.helpers import show_status_and_response

NEW_BOX = schemas.BoxCreate(
    name='Box 4 - Bag of clothes',
    size=BoxSize.Bag,
    essential=True,
    warm=False,
    liquid=False,
)


@pytest.mark.parametrize('box_id', [1, 2, 3])
def test_read_one_box(test_api, box_id):
    response = test_api.get(f'/box_packing/boxes/{box_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_boxes(test_api):
    response = test_api.get('/box_packing/boxes/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_box(test_api):
    response = test_api.post('/box_packing/boxes/', json=NEW_BOX.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_BOX.name

    # Test box was created
    created = test_api.get('/box_packing/boxes/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) == 4


@pytest.mark.parametrize('box_id', [1, 2, 3])
def test_delete_box(test_api, box_id):
    endpoint = f'/box_packing/boxes/{box_id}/'
    box = test_api.get(endpoint)
    assert box.status_code == status.HTTP_200_OK, show_status_and_response(box)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_search_box_items(test_api):
    search_term = 'find'
    search_results = test_api.get('/box_packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = test_api.get('/box_packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 0


def test_box_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a box"""

    # Read all boxes
    all_boxes = test_api.get('/box_packing/boxes/')
    assert all_boxes.status_code == status.HTTP_200_OK, show_status_and_response(all_boxes)
    assert len(all_boxes.json()) == 3

    created_box = test_api.post('/box_packing/boxes/', json=NEW_BOX.model_dump())
    assert created_box.status_code == status.HTTP_201_CREATED, show_status_and_response(created_box)
    assert created_box.json()['name'] == NEW_BOX.name

    # Get created box
    box_id = created_box.json().get('id')
    endpoint = f'/box_packing/boxes/{box_id}/'
    response_box = test_api.get(endpoint)
    assert response_box.status_code == status.HTTP_200_OK, show_status_and_response(response_box)
    assert response_box.json()['name'] == NEW_BOX.name

    # Read all boxes with new box
    all_boxes = test_api.get('/box_packing/boxes/')
    assert all_boxes.status_code == status.HTTP_200_OK, show_status_and_response(all_boxes)
    assert len(all_boxes.json()) == 4

    # Delete box
    deleted_box = test_api.delete(f'/box_packing/boxes/{box_id}/')
    assert deleted_box.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_box)

    # Make sure it's missing
    missing_box = test_api.get(f'/box_packing/boxes/{box_id}')
    assert missing_box.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_box)
