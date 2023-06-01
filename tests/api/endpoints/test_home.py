from tests.helpers import show_status_and_response


def test_read_main(test_api):
    """Test for a valid response"""
    response = test_api.get('')
    assert response.status_code == 200, show_status_and_response(response)
