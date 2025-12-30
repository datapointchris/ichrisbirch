from typing import Any
from typing import TypeVar

from pydantic import BaseModel

from ichrisbirch.config import settings

from .auth import CredentialProvider
from .auth import FlaskSessionProvider
from .auth import InternalServiceProvider
from .auth import UserTokenProvider
from .resource import ResourceClient
from .session import APISession

# Type for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)


class APIClient:
    """Main API client with session management and resource access."""

    def __init__(self, base_url: str | None = None, credential_provider: CredentialProvider | None = None, **session_kwargs):
        self.session = APISession(base_url=base_url, credential_provider=credential_provider, **session_kwargs)
        self._resource_clients: dict[str, ResourceClient] = {}

    def resource(self, name: str, model_class: type[ModelType]) -> ResourceClient[ModelType]:
        """Get or create resource client for given resource name."""
        if name not in self._resource_clients:
            self._resource_clients[name] = ResourceClient(self.session, name, model_class)
        return self._resource_clients[name]

    def request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Direct request method for custom endpoints."""
        return self.session.request(method, endpoint, **kwargs)

    def close(self):
        """Close underlying HTTP client."""
        self.session.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Factory functions for common credential providers
def internal_service_client(service_name: str = 'flask-frontend') -> APIClient:
    """Create client with internal service authentication."""
    provider = InternalServiceProvider(service_name)
    return APIClient(credential_provider=provider)


def user_client(user_id: str, app_id: str | None = None) -> APIClient:
    """Create client with user authentication."""
    app_id = app_id or settings.flask.app_id
    provider = UserTokenProvider(user_id, app_id, settings.auth.internal_service_key)
    return APIClient(credential_provider=provider)


def flask_session_client() -> APIClient:
    """Create client using Flask session for authentication."""
    provider = FlaskSessionProvider()
    return APIClient(credential_provider=provider)


def default_client() -> APIClient:
    """Create client with default authentication (context-aware)."""
    return APIClient()  # Uses _default_provider logic
