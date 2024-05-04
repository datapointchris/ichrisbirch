from tests.helpers import show_status_and_response


def test_get_serverstats(test_api):
    response = test_api.get('/server/')
    assert response.status_code == 200, show_status_and_response(response)
