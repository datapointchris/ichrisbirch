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
        # Retry only a dropped connection: a command that timed out may already have run, and a resend repeats it.
        retry=Retry(NoBackoff(), 1, supported_errors=(redis.ConnectionError,)),
    )
