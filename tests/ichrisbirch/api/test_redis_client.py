import socket
import threading
from collections.abc import Iterator

import pytest
import redis

from ichrisbirch.api.redis_client import get_redis_client
from tests.utils.database import get_test_runner_settings

READ_TIMEOUT_SECONDS = 0.2


@pytest.fixture
def silent_server() -> Iterator[tuple[tuple[str, int], list[socket.socket]]]:
    server = socket.create_server(('127.0.0.1', 0))
    server.settimeout(0.05)
    accepted: list[socket.socket] = []
    stop = threading.Event()

    def accept_without_replying():
        while not stop.is_set():
            try:
                connection, _ = server.accept()
            except TimeoutError:
                continue
            accepted.append(connection)

    acceptor = threading.Thread(target=accept_without_replying, daemon=True)
    acceptor.start()
    yield server.getsockname(), accepted
    stop.set()
    acceptor.join()
    for connection in accepted:
        connection.close()
    server.close()


def test_a_command_that_times_out_is_not_sent_again(silent_server):
    (host, port), accepted = silent_server
    settings = get_test_runner_settings()
    settings.redis.host, settings.redis.port, settings.redis.password = host, port, ''

    with get_redis_client(settings, read_timeout=READ_TIMEOUT_SECONDS) as client, pytest.raises(redis.TimeoutError):
        client.rpush('queue', 'item')

    assert len(accepted) == 1
