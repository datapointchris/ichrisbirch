from datetime import date

from fastapi import status

from tests.helpers import show_status_and_response


def test_index(test_app):
    response = test_app.get('/countdowns/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data


def test_add_countdown(test_app):
    data = dict(
        name='Countdown 4 Computer with notes priority 3',
        notes='Notes Countdown 4',
        due_date=date(2040, 1, 20).isoformat(),
    )
    response = test_app.post('/countdowns/', data=data | {'action': 'add'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data


def test_delete_countdown(test_app):
    response = test_app.post('/countdowns/', data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data
