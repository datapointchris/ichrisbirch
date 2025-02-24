from tests.util import show_status_and_response


def test_get_serverstats(test_api_logged_in):
    response = test_api_logged_in.get('/server/')
    assert response.status_code == 200, show_status_and_response(response)
