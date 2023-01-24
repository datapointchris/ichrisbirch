from ichrisbirch.tests.helpers import endpoint
from ichrisbirch import __version__
import pytest
from ichrisbirch.api.endpoints import health


ENDPOINT = 'health'


@pytest.fixture(scope='module')
def router():
    return health.router


def test_health_check_version(test_app):
    response = test_app.get(endpoint(ENDPOINT))
    assert response.status_code == 200
    assert response.json()['version'] == __version__
