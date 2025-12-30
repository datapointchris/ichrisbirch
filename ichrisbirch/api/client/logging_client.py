"""Enhanced API client with extensive logging to match QueryAPI patterns.

This client preserves all the debugging capabilities and logging detail that exists in QueryAPI while providing modern architecture
patterns.
"""

import logging
from typing import Any
from typing import TypeVar

import httpx
from pydantic import BaseModel

from ichrisbirch.app import utils
from ichrisbirch.config import settings

from .auth import CredentialProvider

ModelType = TypeVar('ModelType', bound=BaseModel)
logger = logging.getLogger(__name__)


class LoggingResourceClient[ModelType]:
    """Resource client with extensive logging matching QueryAPI patterns."""

    def __init__(
        self,
        endpoint: str,
        model_class: type[ModelType],
        session: httpx.Client,
        credential_provider: CredentialProvider,
        base_url: str | None = None,
    ):
        self.endpoint = endpoint
        self.model_class = model_class
        self.session = session
        self.credential_provider = credential_provider
        self.base_url = base_url or settings.api_url

    def _build_url(self, path: Any = None) -> str:
        """Build URL using existing utility function to preserve patterns."""
        return utils.url_builder(self.base_url, self.endpoint, path)

    def _get_headers_for_logging(self, headers: dict[str, str]) -> dict[str, str]:
        """Prepare headers for logging with sensitive data masked."""
        headers_to_log = {}

        # Mask sensitive headers like QueryAPI does
        if user_id := headers.get('X-User-ID'):
            headers_to_log['X-User-ID'] = f'XXXX{user_id[-4:]}'
        if app_id := headers.get('X-Application-ID'):
            headers_to_log['X-Application-ID'] = f'XXXX{app_id[-4:]}'
        if headers.get('X-Internal-Service'):
            headers_to_log['X-Internal-Service'] = headers['X-Internal-Service']
            headers_to_log['X-Service-Key'] = 'XXXXXXXX'  # Always mask service key
        if auth_header := headers.get('Authorization'):
            headers_to_log['Authorization'] = f'Bearer XXXX{auth_header[-8:]}'

        return headers_to_log

    def _prepare_kwargs_for_logging(self, kwargs: dict[str, Any]) -> str:
        """Prepare request kwargs for logging with sensitive data handling."""
        if not kwargs:
            return ''

        kwargs_to_log = {}
        for k, v in kwargs.items():
            if k in ('data', 'json') and settings.ENVIRONMENT == 'production':
                kwargs_to_log[k] = 'XXXXXXXX'  # Mask request body in production
            else:
                kwargs_to_log[k] = v

        return ', '.join([f'{k}={v}' for k, v in kwargs_to_log.items()])

    def _log_request_details(self, method: str, url: str, headers: dict[str, str], **kwargs):
        """Log comprehensive request details matching QueryAPI patterns."""
        headers_to_log = self._get_headers_for_logging(headers)
        kwargs_to_log = self._prepare_kwargs_for_logging(kwargs)

        # Log environment and database info like QueryAPI
        logger.debug(f'running in environment: {settings.ENVIRONMENT} ({settings.sqlalchemy.port})')

        # Log authentication method
        auth_method = 'internal_service' if headers.get('X-Internal-Service') else 'user_auth'
        logger.debug(f'auth method: {auth_method}')

        # Log user info if available
        user_info = 'internal_service' if auth_method == 'internal_service' else 'user_session'
        logger.debug(f'current user in app: {user_info}')

        # Log request details
        logger.debug(f'{method} {url} headers={headers_to_log}{", " + kwargs_to_log if kwargs_to_log else ""}')

    def _handle_request(self, method: str, path: Any = None, **kwargs) -> httpx.Response | None:
        """Make HTTP request with extensive logging and error handling."""
        url = self._build_url(path)

        # Get authentication headers
        headers = self.credential_provider.get_credentials()
        if additional_headers := kwargs.pop('headers', None):
            headers.update(additional_headers)

        # Log request details
        self._log_request_details(method, url, headers, **kwargs)

        try:
            response = self.session.request(method, url, headers=headers, follow_redirects=True, **kwargs)
            response.raise_for_status()

            logger.debug(f'Response status: {response.status_code}')
            return response

        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP {e.response.status_code} error: {e.response.text}')
            return None
        except httpx.RequestError as e:
            logger.error(f'Request error: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return None

    # Core CRUD methods matching QueryAPI interface
    def get_one(self, path: Any = None, **kwargs) -> ModelType | None:
        """Get a single resource, matching QueryAPI.get_one()."""
        response = self._handle_request('GET', path, **kwargs)
        if response and response.content:
            try:
                data = response.json()
                return self.model_class(**data)
            except Exception as e:
                logger.error(f'Failed to parse response as {self.model_class.__name__}: {e}')
                return None
        return None

    def get_many(self, path: Any = None, **kwargs) -> list[ModelType]:
        """Get multiple resources, matching QueryAPI.get_many()."""
        response = self._handle_request('GET', path, **kwargs)
        if response and response.content:
            try:
                data = response.json()
                if isinstance(data, list):
                    return [self.model_class(**item) for item in data]
                else:
                    logger.warning(f'Expected list response, got {type(data)}')
                    return []
            except Exception as e:
                logger.error(f'Failed to parse response as list of {self.model_class.__name__}: {e}')
                return []
        return []

    def get_generic(self, path: Any = None, **kwargs) -> Any | None:
        """Get generic response data, matching QueryAPI.get_generic()."""
        response = self._handle_request('GET', path, **kwargs)
        if response and response.content:
            try:
                return response.json()
            except Exception as e:
                logger.error(f'Failed to parse generic response: {e}')
                return None
        return None

    def post(self, path: Any = None, **kwargs) -> ModelType | None:
        """Create a resource, matching QueryAPI.post()."""
        response = self._handle_request('POST', path, **kwargs)
        if response and response.content:
            try:
                data = response.json()
                return self.model_class(**data)
            except Exception as e:
                logger.error(f'Failed to parse POST response as {self.model_class.__name__}: {e}')
                return None
        return None

    def post_action(self, path: Any = None, **kwargs) -> httpx.Response | None:
        """Post action request, matching QueryAPI.post_action()."""
        return self._handle_request('POST', path, **kwargs)

    def patch(self, path: Any = None, **kwargs) -> ModelType | None:
        """Update a resource, matching QueryAPI.patch()."""
        response = self._handle_request('PATCH', path, **kwargs)
        if response and response.content:
            try:
                data = response.json()
                return self.model_class(**data)
            except Exception as e:
                logger.error(f'Failed to parse PATCH response as {self.model_class.__name__}: {e}')
                return None
        return None

    def delete(self, path: Any = None, **kwargs) -> httpx.Response | None:
        """Delete a resource, matching QueryAPI.delete()."""
        return self._handle_request('DELETE', path, **kwargs)

    # Additional convenience methods
    def create(self, data: dict, **kwargs) -> ModelType | None:
        """Create a resource with data."""
        return self.post(json=data, **kwargs)

    def update(self, id: int, data: dict, **kwargs) -> ModelType | None:
        """Update a resource by ID."""
        return self.patch(id, json=data, **kwargs)

    def get(self, id: int, **kwargs) -> ModelType | None:
        """Get a resource by ID."""
        return self.get_one(id, **kwargs)

    def list(self, **kwargs) -> list[ModelType]:
        """List resources with optional query parameters."""
        if kwargs:
            kwargs['params'] = kwargs
        return self.get_many(**kwargs)


class LoggingAPIClient:
    """Main API client with extensive logging, matching QueryAPI patterns."""

    def __init__(self, credential_provider: CredentialProvider, base_url: str | None = None):
        self.credential_provider = credential_provider
        self.base_url = base_url or settings.api_url
        self.session = httpx.Client(timeout=30.0)

        logger.debug(f'Created LoggingAPIClient with base_url: {self.base_url}')
        logger.debug(f'Authentication provider: {type(credential_provider).__name__}')

    def resource(self, endpoint: str, model_class: type[ModelType]) -> LoggingResourceClient[ModelType]:
        """Get a resource client for the specified endpoint and model."""
        logger.debug(f'Creating resource client for endpoint: {endpoint}, model: {model_class.__name__}')
        return LoggingResourceClient(
            endpoint=endpoint,
            model_class=model_class,
            session=self.session,
            credential_provider=self.credential_provider,
            base_url=self.base_url,
        )

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Factory functions for LoggingAPIClient
def logging_internal_service_client(service_name: str = 'flask-frontend', base_url: str | None = None) -> LoggingAPIClient:
    """Create an internal service client with extensive logging."""
    from .auth import InternalServiceProvider

    provider = InternalServiceProvider(service_name)
    return LoggingAPIClient(provider, base_url)


def logging_user_client(user_id: str, app_id: str | None = None, base_url: str | None = None) -> LoggingAPIClient:
    """Create a user client with extensive logging."""
    from .auth import UserTokenProvider

    actual_app_id = app_id or settings.flask.app_id
    provider = UserTokenProvider(user_id, actual_app_id, settings.auth.internal_service_key)
    return LoggingAPIClient(provider, base_url)


def logging_flask_session_client(base_url: str | None = None) -> LoggingAPIClient:
    """Create a Flask session client with extensive logging."""
    from .auth import FlaskSessionProvider

    provider = FlaskSessionProvider()
    return LoggingAPIClient(provider, base_url)
