import pytest

from ichrisbirch.api.endpoints import main


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return main.router


def test_read_main(test_app):
    """Test for a valid response"""
    response = test_app.get('')
    assert response.status_code == 200
