from tests.util import show_status_and_response


def test_read_main(test_api_logged_in):
    response = test_api_logged_in.get('')
    assert response.status_code == 200, show_status_and_response(response)
