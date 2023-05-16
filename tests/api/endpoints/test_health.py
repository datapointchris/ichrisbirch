import pytest

from ichrisbirch.api import endpoints
from ichrisbirch.config import get_settings

settings = get_settings()


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return endpoints.health.router


def test_health_check_version(test_api):
    """Test if the version provided by health check matches project version"""
    response = test_api.get('/health/')
    assert response.status_code == 200
    assert response.json()['version'] == settings.version
