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
        # One immediate retry replaces a pooled connection the server closed, with no backoff sleep.
        retry=Retry(NoBackoff(), 1),
    )
