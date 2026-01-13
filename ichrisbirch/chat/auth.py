import logging
from collections.abc import Generator
from contextlib import contextmanager

import httpx
import pendulum

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.logging_client import logging_internal_service_client
from ichrisbirch.app.utils import url_builder
from ichrisbirch.config import Settings

logger = logging.getLogger(__name__)


class ChatAuthClient:
    def __init__(self, settings: Settings):
        self.api_url = settings.api_url
        self.token_url = f'{self.api_url}/auth/token/'
        self.users_url = f'{self.api_url}/users/'

    @contextmanager
    def safe_request_client(self) -> Generator[httpx.Client, None, None]:
        """Provide an HTTP client with automatic cleanup.

        Exceptions are logged and propagated to callers.
        Callers must handle exceptions appropriately.
        """
        client = httpx.Client(follow_redirects=True)
        try:
            yield client
        except httpx.HTTPStatusError as e:
            logger.warning(f'HTTP error occurred: {e.response.status_code} - {e.response.text}')
            raise
        except httpx.RequestError as e:
            logger.error(f'Request error occurred: {e}')
            raise
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
            return response.json().get('access_token')

    def login_username(self, username: str, password: str):
        """Login user with username/password using modern internal service client."""
        # Use the new logging internal service client instead of service account
        with logging_internal_service_client() as client:
            users = client.resource('users', schemas.User)

            # Look up user by email using the new client
            if user_data := users.get_generic(['email', username]):
                user = models.User(**user_data)
                if user.check_password(password):
                    logger.debug(f'logged in user: {user.name} - last previous login: {user.last_login}')
                    try:
                        users.patch([user.id], json={'last_login': pendulum.now().for_json()})
                        logger.debug(f'updated last login for user: {user.name}')
                    except Exception as e:
                        # Silent failure: last_login update is non-critical
                        # User cannot act on this, don't block login or show error
                        # System log captures issue for debugging
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
