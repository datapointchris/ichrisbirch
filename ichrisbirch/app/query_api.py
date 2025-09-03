import logging
from contextlib import suppress
from typing import Any
from typing import TypeVar

import httpx
from flask import Flask
from flask import session
from flask_login import current_user
from pydantic import BaseModel

from ichrisbirch import models
from ichrisbirch.app import utils
from ichrisbirch.config import settings

ModelType = TypeVar('ModelType', bound=BaseModel)
logger = logging.getLogger(__name__)


class QueryAPI[ModelType]:
    """
    user: solely for adding the headers to authenticate with the api
    WARNING: setting the default user to `current_user` causes the API to make hundreds of identical requests.
    """

    def __init__(
        self,
        base_endpoint: str,
        response_model: type[ModelType],
        user: models.User | Any = None,
        app: Flask | None = None,
        use_internal_auth: bool = False,
    ):
        self.base_endpoint = base_endpoint
        self.response_model = response_model
        self.use_internal_auth = use_internal_auth

        # Improved user resolution - check outside of constructor when possible
        if use_internal_auth:
            self.user = None
        else:
            self.user = user or self._resolve_current_user()

        # Simplified app/settings resolution for containerized setup
        self.app = app
        self.client = httpx.Client()

    def _resolve_current_user(self):
        """Safely resolve current user without causing circular dependencies."""
        try:
            return current_user if (current_user and current_user.is_authenticated) else None
        except RuntimeError:
            # Outside Flask context - this is fine for testing
            logger.debug('No Flask context available for current_user')
            return None

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers based on auth type."""
        if self.use_internal_auth:
            # Internal service authentication
            return {
                'X-Internal-Service': 'flask-frontend',
                'X-Service-Key': getattr(settings.auth, 'internal_service_key', 'dev-key'),
            }
        else:
            # User-based authentication
            user_id = None
            if self.user:
                user_id = self.user.get_id() or ''
            else:
                # Fallback to session if no user provided
                try:
                    if session_user_id := session.get('_user_id'):
                        user_id = session_user_id
                        logger.info(f'found user id {user_id} in session')
                except RuntimeError:
                    logger.warning('could not access session, outside of request context')

            return {
                'X-User-ID': user_id or '',
                'X-Application-ID': settings.flask.app_id,
            }

    def _get_api_url(self) -> str:
        """Get API URL, preferring Flask app settings over global settings."""
        with suppress(ImportError):
            from flask import current_app

            if current_app and 'SETTINGS' in current_app.config:
                return current_app.config['SETTINGS'].api_url
        return settings.api_url

    def _handle_request(self, method: str, endpoint: Any | None = None, **kwargs):
        """Enhanced request handler with preserved logging and functionality."""
        url = utils.url_builder(self._get_api_url(), self.base_endpoint, endpoint)

        # Get authentication headers
        headers = self._get_auth_headers()

        # Preserve your detailed logging
        headers_to_log = {
            'X-User-ID': f'XXXX{headers.get("X-User-ID", "")[-4:]}',
            'X-Application-ID': f'XXXX{settings.flask.app_id[-4:]}',
        }

        kwargs_to_log = ''
        if additional_headers := kwargs.pop('headers', None):
            headers.update(**additional_headers)
            headers_to_log.update(**additional_headers)
        if kwargs:
            if settings.ENVIRONMENT == 'production':
                kwargs_to_log = ', '.join([f'{k}=XXXXXXXX' for k in kwargs])
            else:
                kwargs_to_log = ', '.join([f'{k}={v}' for k, v in kwargs.items()])

        logger.debug(f'running in environment: {settings.ENVIRONMENT} ({settings.sqlalchemy.port})')
        logger.debug(f'current user in app: {f"{self.user.email} - {self.user.alternative_id}" if self.user else "None"}')
        logger.debug(f'auth method: {"internal_service" if self.use_internal_auth else "user_auth"}')
        logger.debug(f'{method} {url} headers={headers_to_log}{", " + kwargs_to_log if kwargs_to_log else ""}')

        try:
            return self.client.request(method, url, headers=headers, **kwargs, follow_redirects=True).raise_for_status()
        except httpx.HTTPError as e:
            logger.error(e)
            return None

    def get_one(self, endpoint: Any | None = None, **kwargs) -> ModelType | None:
        response = self._handle_request('GET', endpoint, **kwargs)
        if response and response.json():
            return self.response_model(**response.json())
        return None

    def get_many(self, endpoint: Any | None = None, **kwargs) -> list[ModelType]:
        if response := self._handle_request('GET', endpoint, **kwargs):
            return [self.response_model(**result) for result in response.json()]
        return []

    def get_generic(self, endpoint: Any | None = None, **kwargs) -> Any | None:
        """Use this method when the response is not a single ModelType."""
        response = self._handle_request('GET', endpoint, **kwargs)
        if response and response.json():
            return response.json()
        return None

    def post(self, endpoint: Any | None = None, **kwargs):
        if response := self._handle_request('POST', endpoint, **kwargs):
            return self.response_model(**response.json())
        return None

    def post_action(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('POST', endpoint, **kwargs)

    def patch(self, endpoint: Any | None = None, **kwargs):
        if response := self._handle_request('PATCH', endpoint, **kwargs):
            return self.response_model(**response.json())
        return None

    def delete(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('DELETE', endpoint, **kwargs)
