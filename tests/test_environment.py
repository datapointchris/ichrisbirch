import pytest

from tests.environment import PrivateServices
from tests.utils.database import get_test_runner_settings


class StubContainer:
    def __init__(self, failure: Exception | None = None):
        self.failure = failure
        self.running = False

    def start(self):
        if self.failure:
            raise self.failure
        self.running = True
        return self

    def stop(self):
        self.running = False


def test_a_service_that_fails_to_start_ends_the_session_and_removes_the_one_that_started():
    services = PrivateServices(get_test_runner_settings())
    services.redis = StubContainer()
    services.postgres = StubContainer(RuntimeError('port is already allocated'))

    with pytest.raises(pytest.exit.Exception) as ended, services:
        pass

    assert 'port is already allocated' in str(ended.value)
    assert services.redis.running is False
