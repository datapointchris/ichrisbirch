from tests.helpers import show_status_and_response


def test_get_server_stats(test_api):
    response = test_api.get('/server_stats/')
    assert response.status_code == 200, show_status_and_response(response)
