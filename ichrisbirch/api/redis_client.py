import redis

from ichrisbirch.config import Settings


def get_redis_client(settings: Settings) -> redis.Redis:
    return redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password or None,
        db=settings.redis.db,
        decode_responses=True,
    )
