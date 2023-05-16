import pytest

from ichrisbirch.api import endpoints


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return endpoints.home.router


def test_read_main(test_api):
    """Test for a valid response"""
    response = test_api.get('')
    assert response.status_code == 200
