import pytest

from ichrisbirch.api.endpoints import health
from ichrisbirch.config import settings
from tests.helpers import format_endpoint

ENDPOINT = 'health'


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return health.router


def test_health_check_version(test_app):
    """Test if the version provided by health check matches project version"""
    response = test_app.get(format_endpoint(ENDPOINT))
    assert response.status_code == 200
    assert response.json()['version'] == settings.VERSION
