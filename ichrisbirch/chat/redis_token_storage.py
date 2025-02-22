import logging
from typing import Protocol

import redis

logger = logging.getLogger('chat.storage')


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
        logger.info(f'Saved {token_type} token for user {user_id} in Redis')

    def get_token(self, user_id: str, token_type: str) -> str | None:
        """Retrieve token from Redis."""
        key = f'{user_id}:{token_type}'
        if token := self.redis.get(key):
            logger.info(f'Retrieved {token_type} token for user {user_id} from Redis')
            return str(token)
        logger.warning(f'No {token_type} token found for user {user_id}')
        return None

    def delete_token(self, user_id: str, token_type: str):
        """Delete token from Redis."""
        key = f'{user_id}:{token_type}'
        self.redis.delete(key)
        logger.info(f'Deleted {token_type} token for user {user_id} from Redis')
