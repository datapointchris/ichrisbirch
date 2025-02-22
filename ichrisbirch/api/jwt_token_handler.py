import logging
from datetime import timedelta

import jwt
import pendulum

from ichrisbirch.config import settings

logger = logging.getLogger('api.token_handler')


class JWTTokenHandler:
    def __init__(
        self,
        access_token_expire_delta=settings.auth.access_token_expire,
        refresh_token_expire_delta=settings.auth.refresh_token_expire,
        secret_key=settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_delta = access_token_expire_delta
        self.refresh_token_expire_delta = refresh_token_expire_delta

    def _generate_jwt(self, user_id: str, expires_delta: timedelta):
        payload = {'sub': user_id, 'iat': pendulum.now(), 'exp': pendulum.now() + expires_delta}
        token = jwt.encode(payload=payload, key=self.secret_key, algorithm=self.algorithm)
        return token

    def create_access_token(self, user_id: str):
        return self._generate_jwt(user_id, expires_delta=self.access_token_expire_delta)

    def create_refresh_token(self, user_id: str):
        return self._generate_jwt(user_id, expires_delta=self.refresh_token_expire_delta)

    def store_refresh_token(self, user_id: str, refresh_token: str):
        with open('rfrtkns.txt', 'a') as f:
            f.write(f'{user_id}: {refresh_token}\n')

    def retrieve_refresh_token(self, user_id: str) -> str:
        with open('rfrtkns.txt') as f:
            for line in f:
                if line.startswith(user_id):
                    return line.split(': ')[1].strip()
        return ''

    def delete_refresh_token(self, user_id: str):
        with open('rfrtkns.txt') as f:
            lines = f.readlines()
        with open('rfrtkns.txt', 'w') as f:
            for line in lines:
                if line.startswith(user_id):
                    logger.info(f'deleting refresh token for user: {user_id}')
                if not line.startswith(user_id):
                    f.write(line)
