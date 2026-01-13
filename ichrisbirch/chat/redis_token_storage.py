from typing import Protocol

import redis
import structlog

logger = structlog.get_logger()


class TokenStorage(Protocol):
    """Protocol for token storage implementations."""

    def save_token(self, user_id: str, token: str, token_type: str) -> None:
        """Store a token."""

    def get_token(self, user_id: str, token_type: str) -> str | None:
        """Retrieve a token."""

    def delete_token(self, user_id: str, token_type: str) -> None:
        """Delete a token."""


class FakeTokenStorage(TokenStorage):
    """Fake token storage that does nothing."""

    def save_token(self, user_id: str, token: str, token_type: str) -> None:
        pass

    def get_token(self, user_id: str, token_type: str) -> str | None:
        return None

    def delete_token(self, user_id: str, token_type: str) -> None:
        pass


class RedisTokenStorage:
    def __init__(self):
        self.redis = redis.Redis()
        days_30 = 60 * 60 * 24 * 30
        self.token_expiry = days_30

    def save_token(self, user_id: str, token: str, token_type: str):
        """Store token in Redis with user_id as key."""
        key = f'{user_id}:{token_type}'
        self.redis.set(key, token, ex=self.token_expiry)
        logger.info('redis_token_saved', user_id=user_id, token_type=token_type)

    def get_token(self, user_id: str, token_type: str) -> str | None:
        """Retrieve token from Redis."""
        key = f'{user_id}:{token_type}'
        if token := self.redis.get(key):
            logger.info('redis_token_retrieved', user_id=user_id, token_type=token_type)
            return str(token)
        logger.warning('redis_token_not_found', user_id=user_id, token_type=token_type)
        return None

    def delete_token(self, user_id: str, token_type: str):
        """Delete token from Redis."""
        key = f'{user_id}:{token_type}'
        self.redis.delete(key)
        logger.info('redis_token_deleted', user_id=user_id, token_type=token_type)
