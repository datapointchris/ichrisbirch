import copy

from ichrisbirch.app.routes.events import EVENTS_API_URL
from tests.helpers import show_status_and_response
from tests.testing_data.events import CREATE_DATA


def test_index(test_app):
    response = test_app.get(EVENTS_API_URL + '/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_crud_add(test_app):
    response = test_app.post(EVENTS_API_URL + '/crud/', data=CREATE_DATA | {'method': 'add'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/events/'
    assert b'<title>Events</title>' in response.data


def test_crud_add_string_date(test_app):
    response = test_app.post(
        EVENTS_API_URL + '/crud/',
        data=copy.deepcopy(CREATE_DATA) | {'date': '2026-10-05', 'method': 'add'},
        follow_redirects=True,
    )
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/events/'
    assert b'<title>Events</title>' in response.data


def test_crud_delete(test_app):
    response = test_app.post(EVENTS_API_URL + '/crud/', data={'id': 1, 'method': 'delete'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/events/'
    assert b'<title>Events</title>' in response.data
