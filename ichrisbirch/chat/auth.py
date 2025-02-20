import logging
from contextlib import contextmanager
from typing import Generator

import httpx
import pendulum

from ichrisbirch import models
from ichrisbirch.app.utils import url_builder
from ichrisbirch.chat.redis_token_storage import RedisTokenStorage
from ichrisbirch.config import Settings

logger = logging.getLogger('chat.auth')


class ChatAuthClient:
    def __init__(self, settings: Settings):
        self.api_url = settings.api_url
        self.token_url = f'{self.api_url}/auth/token/'
        self.users_url = f'{self.api_url}/users/'
        self.token_storage = RedisTokenStorage(host=settings.redis.host, port=settings.redis.port, db=settings.redis.db)

    @contextmanager
    def safe_request_client(self) -> Generator[httpx.Client, None, None]:
        client = httpx.Client(follow_redirects=True)
        try:
            yield client
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP error occurred: {e.response.status_code} - {e.response.text}')
            return None
        except httpx.RequestError as e:
            logger.error(f'Request error occurred: {e}')
            return None
        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')
            return None
        finally:
            client.close()

    def request_jwt_tokens(self, user: models.User, password: str):
        request_data = {'username': user.email, 'password': password}
        with self.safe_request_client() as client:
            return client.post(self.token_url, data=request_data).raise_for_status().json()

    def validate_jwt_token(self, token: str):
        logger.debug(f'validating access token: {token}')
        validate_url = url_builder(self.token_url, 'validate')
        headers = {'Authorization': f'Bearer {token}'}
        with self.safe_request_client() as client:
            return client.get(validate_url, headers=headers).raise_for_status().status_code == httpx.codes.OK

    def refresh_access_token(self, token: str):
        logger.debug(f'getting access token with refresh token: {token}')
        headers = {'Authorization': f'Bearer {token}'}
        refresh_url = url_builder(self.token_url, 'refresh')
        with self.safe_request_client() as client:
            response = client.post(refresh_url, headers=headers).raise_for_status()
            return response.json().get("access_token")

    def login_user(self, username: str, password: str):
        user_login_url = url_builder(self.users_url, 'email', username)
        with self.safe_request_client() as client:
            user_data = client.get(user_login_url).raise_for_status().json()
            if user := models.User(**user_data):
                if user.check_password(password=password):
                    logger.debug(f'logged in user: {user.name} - last previous login: {user.last_login}')
                    client.patch(url_builder(self.users_url, user.id), json={'last_login': pendulum.now().for_json()})
                    return user
                else:
                    logger.warning(f'incorrect password for user: {user.email}')
            else:
                logger.warning(f'user with email {username} not found')
        return None

    def logout_user(self, user: models.User, token: str):
        headers = {'X-User-ID': user.get_id()}
        logger.debug(f'logging out user: {user} with token {token[:10]}')
        self.delete_access_token(user.get_id())
        self.delete_refresh_token(user.get_id())
        user_logout_url = url_builder(self.api_url, 'auth', 'logout')
        with self.safe_request_client() as client:
            client.get(user_logout_url, headers=headers).raise_for_status()

    def save_access_token(self, user_id: str, token: str):
        self.token_storage.save_token(user_id, token, 'access')

    def retrieve_access_token(self, user_id: str) -> str | None:
        return self.token_storage.get_token(user_id, 'access')

    def delete_access_token(self, user_id: str):
        self.token_storage.delete_token(user_id, 'access')

    def save_refresh_token(self, user_id: str, token: str):
        self.token_storage.save_token(user_id, token, 'refresh')

    def retrieve_refresh_token(self, user_id: str) -> str | None:
        return self.token_storage.get_token(user_id, 'refresh')

    def delete_refresh_token(self, user_id: str):
        self.token_storage.delete_token(user_id, 'refresh')
