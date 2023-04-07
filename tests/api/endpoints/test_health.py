import pytest

from ichrisbirch.api.endpoints import health
from ichrisbirch.config import settings


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return health.router


def test_health_check_version(test_app):
    """Test if the version provided by health check matches project version"""
    response = test_app.get('/health/')
    assert response.status_code == 200
    assert response.json()['version'] == settings.VERSION
