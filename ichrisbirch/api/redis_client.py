import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from ichrisbirch.config import Settings

CONNECT_TIMEOUT_SECONDS = 2
REQUEST_READ_TIMEOUT_SECONDS = 2


def get_redis_client(settings: Settings, *, read_timeout: float) -> redis.Redis:
    return redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password or None,
        db=settings.redis.db,
        decode_responses=True,
        socket_connect_timeout=CONNECT_TIMEOUT_SECONDS,
        socket_timeout=read_timeout,
        # Timeouts are not retried: the server may already have run the command, and a resend would queue a bulk import twice.
        retry=Retry(NoBackoff(), 1, supported_errors=(redis.ConnectionError,)),
    )
