from ichrisbirch.app.routes.countdowns import COUNTDOWNS_URL
from tests.helpers import show_status_and_response
from tests.testing_data.countdowns import CREATE_DATA


def test_index(test_app):
    response = test_app.get(COUNTDOWNS_URL + '/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data


def test_crud_add(test_app):
    response = test_app.post(COUNTDOWNS_URL + '/crud/', data=CREATE_DATA | {'method': 'add'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/countdowns/'
    assert b'<title>Countdowns</title>' in response.data


def test_crud_delete(test_app):
    response = test_app.post(COUNTDOWNS_URL + '/crud/', data={'id': 1, 'method': 'delete'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/countdowns/'
    assert b'<title>Countdowns</title>' in response.data
