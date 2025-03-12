import logging
from contextlib import contextmanager
from typing import Generator

import httpx
import pendulum

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.app.query_api import APIServiceAccount
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.app.utils import url_builder
from ichrisbirch.config import Settings

logger = logging.getLogger('chat.auth')
service_user = APIServiceAccount()


class ChatAuthClient:
    def __init__(self, settings: Settings):
        self.api_url = settings.api_url
        self.token_url = f'{self.api_url}/auth/token/'
        self.users_url = f'{self.api_url}/users/'

    @contextmanager
    def safe_request_client(self) -> Generator[httpx.Client, None, None]:
        client = httpx.Client(follow_redirects=True)
        try:
            yield client
        except httpx.HTTPStatusError as e:
            logger.warning(f'HTTP error occurred: {e.response.status_code} - {e.response.text}')
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
        logger.debug(f'validating access token: {token[-10:]}')
        validate_url = url_builder(self.token_url, 'validate')
        headers = {'Authorization': f'Bearer {token}'}
        with self.safe_request_client() as client:
            sc = client.get(validate_url, headers=headers).raise_for_status().status_code
            logger.warning(f'status code: {sc}')
            return sc == 200

    def refresh_access_token(self, token: str):
        logger.debug(f'getting access token with refresh token: {token[-10:]}')
        headers = {'Authorization': f'Bearer {token}'}
        refresh_url = url_builder(self.token_url, 'refresh')
        with self.safe_request_client() as client:
            response = client.post(refresh_url, headers=headers).raise_for_status()
            return response.json().get("access_token")

    def login_username(self, username: str, password: str):
        users_api = QueryAPI(base_url='users', response_model=schemas.User)
        service_user.get_user()
        service_account_users_api = QueryAPI(base_url='users', response_model=schemas.User, user=service_user.user)

        if user := service_account_users_api.get_one(['email', username]):
            user = models.User(**user.model_dump())
            if user.check_password(password):
                logger.debug(f'logged in user: {user.name} - last previous login: {user.last_login}')
                try:
                    users_api = QueryAPI(base_url='users', response_model=schemas.User)
                    users_api.patch([user.id], json={'last_login': pendulum.now().for_json()})
                    logger.debug(f'updated last login for user: {user.name}')
                except Exception as e:
                    logger.error(f'error updating last login for user {user.name}: {e}')
                return user
            else:
                logger.warning(f'incorrect password for user: {user.email}')
        else:
            logger.warning(f'user with email {username} not found')
        return None

    def login_token(self, token: str):
        user_login_url = url_builder(self.users_url, 'me')
        headers = {'Authorization': f'Bearer {token}'}
        with self.safe_request_client() as client:
            user_data = client.get(user_login_url, headers=headers).raise_for_status().json()
            if user := models.User(**user_data):
                logger.debug(f'logged in user: {user.email} - last previous login: {user.last_login}')
                client.patch(url_builder(self.users_url, user.id), json={'last_login': pendulum.now().for_json()})
                return user
            else:
                logger.warning('invalid token login attempt')
        return None

    def logout_user(self, user: models.User, token: str):
        headers = {'X-User-ID': user.get_id()}
        logger.debug(f'logging out user: {user.email} with token {token[-10:]}')
        user_logout_url = url_builder(self.api_url, 'auth', 'logout')
        with self.safe_request_client() as client:
            client.get(user_logout_url, headers=headers).raise_for_status()
