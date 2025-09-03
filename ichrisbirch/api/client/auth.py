from abc import ABC
from abc import abstractmethod

from flask import current_app
from flask import has_request_context
from flask import session

from ichrisbirch.config import settings


class CredentialProvider(ABC):
    """Abstract base for credential providers."""

    @abstractmethod
    def get_credentials(self) -> dict[str, str]:
        """Get authentication credentials as headers."""
        pass

    @abstractmethod
    def refresh_if_needed(self) -> None:
        """Refresh credentials if they're expired."""
        pass


class InternalServiceProvider(CredentialProvider):
    """Credentials for internal service-to-service calls."""

    def __init__(self, service_name: str = 'flask-frontend'):
        self.service_name = service_name
        # Use Flask app's test-compatible settings if available
        try:
            if current_app and 'SETTINGS' in current_app.config:
                self.service_key = current_app.config['SETTINGS'].auth.internal_service_key
            else:
                self.service_key = settings.auth.internal_service_key
        except (RuntimeError, ImportError):
            # Outside Flask context or Flask not available - use global settings
            self.service_key = settings.auth.internal_service_key

    def get_credentials(self) -> dict[str, str]:
        return {
            'X-Internal-Service': self.service_name,
            'X-Service-Key': self.service_key,
        }

    def refresh_if_needed(self) -> None:
        # Internal service keys don't expire
        pass


class UserTokenProvider(CredentialProvider):
    """Credentials for user-authenticated requests."""

    def __init__(self, user_id: str, app_id: str):
        self.user_id = user_id
        self.app_id = app_id
        self._token = None
        self._expires_at = None

    def get_credentials(self) -> dict[str, str]:
        self.refresh_if_needed()
        return {
            'X-User-ID': self.user_id,
            'X-Application-ID': self.app_id,
            'Authorization': f'Bearer {self._token}' if self._token else '',
        }

    def refresh_if_needed(self) -> None:
        # Check if token needs refresh
        if self._token_expired():
            self._refresh_token()

    def _token_expired(self) -> bool:
        # Get token from database or token service
        # This should be implemented based on your specific token storage
        return False

    def _refresh_token(self) -> None:
        # Refresh token logic
        pass


class FlaskSessionProvider(CredentialProvider):
    """Credentials from Flask session (for your current use case)."""

    def __init__(self):
        self.has_context = has_request_context()

    def get_credentials(self) -> dict[str, str]:
        if not self.has_context:
            return {}

        user_id = session.get('_user_id', '')
        return {
            'X-User-ID': user_id,
            'X-Application-ID': settings.flask.app_id,
        }

    def refresh_if_needed(self) -> None:
        # Flask sessions don't need refresh
        pass
