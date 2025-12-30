"""Improved API client for Flask-to-FastAPI communication."""

import logging
from typing import Any
from typing import TypeVar
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from ichrisbirch.config import settings

logger = logging.getLogger(__name__)

ModelType = TypeVar('ModelType', bound=BaseModel)


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class AuthenticationError(APIClientError):
    """Authentication-related errors."""

    pass


class NotFoundError(APIClientError):
    """Resource not found errors."""

    pass


class InternalServiceAuth:
    """Authentication provider for internal service calls."""

    def __init__(self, service_name: str = 'flask-frontend'):
        self.service_name = service_name
        self.service_key = getattr(settings.auth, 'internal_service_key', None)

        if not self.service_key:
            raise ValueError('Internal service key not configured')

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for internal service calls."""
        if not self.service_key:
            raise ValueError('Service key not available')

        return {
            'X-Internal-Service': self.service_name,
            'X-Service-Key': self.service_key,
        }


class UserAuth:
    """Authentication provider for user-based calls."""

    def __init__(self, user_id: str, app_id: str, service_key: str):
        self.user_id = user_id
        self.app_id = app_id
        self.service_key = service_key

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for user calls."""
        return {
            'X-User-ID': self.user_id,
            'X-Application-ID': self.app_id,
            'X-Service-Key': self.service_key,
        }


class ResourceClient[ModelType: BaseModel]:
    """Base client for API resources."""

    def __init__(self, api_client: 'APIClient', endpoint: str, model_class: type[ModelType]):
        self.api = api_client
        self.endpoint = endpoint
        self.model_class = model_class

    def get_by_id(self, resource_id: int) -> ModelType | None:
        """Get a resource by ID."""
        try:
            response = self.api.get(f'{self.endpoint}/{resource_id}/')
            return self.model_class(**response) if response else None
        except NotFoundError:
            return None

    def get_all(self, **params) -> list[ModelType]:
        """Get all resources with optional query parameters."""
        response = self.api.get(f'{self.endpoint}/', params=params)
        return [self.model_class(**item) for item in response] if response else []

    def create(self, data: dict[str, Any]) -> ModelType | None:
        """Create a new resource."""
        response = self.api.post(f'{self.endpoint}/', json=data)
        return self.model_class(**response) if response else None

    def update(self, resource_id: int, data: dict[str, Any]) -> ModelType | None:
        """Update a resource."""
        response = self.api.patch(f'{self.endpoint}/{resource_id}/', json=data)
        return self.model_class(**response) if response else None

    def delete(self, resource_id: int) -> bool:
        """Delete a resource."""
        return self.api.delete(f'{self.endpoint}/{resource_id}/')


class UsersClient(ResourceClient):
    """Specialized client for user operations."""

    def get_by_email(self, email: str) -> BaseModel | None:
        """Get user by email address."""
        try:
            response = self.api.get(f'{self.endpoint}/email/{email}/')
            return self.model_class(**response) if response else None
        except NotFoundError:
            return None

    def get_by_alt_id(self, alt_id: str) -> BaseModel | None:
        """Get user by alternative ID."""
        try:
            response = self.api.get(f'{self.endpoint}/alt/{alt_id}/')
            return self.model_class(**response) if response else None
        except NotFoundError:
            return None

    def get_me(self) -> BaseModel | None:
        """Get current user (requires user authentication)."""
        try:
            response = self.api.get(f'{self.endpoint}/me/')
            return self.model_class(**response) if response else None
        except NotFoundError:
            return None

    def update_preferences(self, user_id: int | None = None, preferences: dict[str, Any] | None = None) -> BaseModel | None:
        """Update user preferences."""
        endpoint = f'{self.endpoint}/me/preferences/' if user_id is None else f'{self.endpoint}/{user_id}/preferences/'
        response = self.api.patch(endpoint, json=preferences)
        return self.model_class(**response) if response else None


class APIClient:
    """Main API client for communicating with FastAPI backend."""

    def __init__(self, base_url: str | None = None, auth_provider=None):
        self.base_url = base_url or settings.api_url
        self.auth_provider = auth_provider or InternalServiceAuth()
        self.client = httpx.Client(follow_redirects=True)

        # Set default headers
        self.client.headers.update(self.auth_provider.get_headers())

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request and handle common errors."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))

        try:
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()

            # Handle empty responses (like DELETE)
            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f'Resource not found: {endpoint}') from e
            elif e.response.status_code == 401:
                raise AuthenticationError(f'Authentication failed: {endpoint}') from e
            else:
                logger.error(f'HTTP error {e.response.status_code} for {method} {url}: {e.response.text}')
                raise APIClientError(f'API request failed: {e.response.status_code}') from e

        except httpx.RequestError as e:
            logger.error(f'Request error for {method} {url}: {e}')
            raise APIClientError(f'Request failed: {e}') from e

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint: str, json: dict[str, Any] | None = None, **kwargs) -> Any:
        """Make POST request."""
        return self._make_request('POST', endpoint, json=json, **kwargs)

    def patch(self, endpoint: str, json: dict[str, Any] | None = None, **kwargs) -> Any:
        """Make PATCH request."""
        return self._make_request('PATCH', endpoint, json=json, **kwargs)

    def delete(self, endpoint: str) -> bool:
        """Make DELETE request."""
        try:
            self._make_request('DELETE', endpoint)
            return True
        except APIClientError:
            return False

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Factory functions for common use cases
def get_internal_api_client() -> APIClient:
    """Get API client with internal service authentication."""
    return APIClient(auth_provider=InternalServiceAuth())


def get_user_api_client(user_id: str) -> APIClient:
    """Get API client with user authentication."""
    auth = UserAuth(user_id=user_id, app_id=settings.flask.app_id, service_key=settings.auth.internal_service_key)
    return APIClient(auth_provider=auth)


def get_users_client(auth_provider=None) -> UsersClient:
    """Get specialized users client."""
    from ichrisbirch import schemas  # Import here to avoid circular imports

    api_client = APIClient(auth_provider=auth_provider or InternalServiceAuth())
    return UsersClient(api_client, '/users', schemas.User)
