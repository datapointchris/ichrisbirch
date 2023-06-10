from ichrisbirch.config import get_settings
from tests.helpers import show_status_and_response

settings = get_settings()


def test_health_check_version(test_api):
    response = test_api.get('/health/')
    assert response.status_code == 200, show_status_and_response(response)
