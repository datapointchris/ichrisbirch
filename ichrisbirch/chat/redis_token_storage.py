import logging
from typing import Optional

import redis

logger = logging.getLogger('chat.storage')


class RedisTokenStorage:
    def __init__(self, host: str, port: int, db: int):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        days_30 = 60 * 60 * 24 * 30
        self.token_expiry = days_30

    def save_token(self, user_id: str, token: str, token_type: str):
        """Store token in Redis with user_id as key."""
        key = f'{user_id}:{token_type}'
        self.redis.set(key, token, ex=self.token_expiry)
        logger.info(f'Saved {token_type} token for user {user_id} in Redis')

    def get_token(self, user_id: str, token_type: str) -> Optional[str]:
        """Retrieve token from Redis."""
        key = f'{user_id}:{token_type}'
        if token := self.redis.get(key):
            logger.info(f'Retrieved {token_type} token for user {user_id} from Redis')
            return token
        logger.warning(f'No {token_type} token found for user {user_id}')
        return None

    def delete_token(self, user_id: str, token_type: str):
        """Delete token from Redis."""
        key = f'{user_id}:{token_type}'
        self.redis.delete(key)
        logger.info(f'Deleted {token_type} token for user {user_id} from Redis')
