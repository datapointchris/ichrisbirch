from fastapi import status

from tests.util import show_status_and_response


def test_get_serverstats(test_app):
    response = test_app.get('/admin/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
