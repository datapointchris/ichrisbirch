from fastapi import status

from tests.helpers import show_status_and_response


def test_get_serverstats(test_app):
    response = test_app.get('/server/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
