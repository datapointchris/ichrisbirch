from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING

from flask import current_app
from flask import has_request_context
from flask import session

from ichrisbirch.config import get_settings

if TYPE_CHECKING:
    from ichrisbirch.config import Settings


def _get_settings_with_fallback(explicit_settings: 'Settings | None' = None) -> 'Settings':
    """Get settings with priority: explicit > Flask context > global."""
    if explicit_settings:
        return explicit_settings
    with suppress(RuntimeError):
        if current_app and 'SETTINGS' in current_app.config:
            return current_app.config['SETTINGS']
    return get_settings()


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

    def __init__(self, service_name: str = 'flask-frontend', settings: 'Settings | None' = None):
        self.service_name = service_name
        self._settings = _get_settings_with_fallback(settings)
        self.service_key = self._settings.auth.internal_service_key

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

    def __init__(self, user_id: str, app_id: str, service_key: str):
        self.user_id = user_id
        self.app_id = app_id
        self.service_key = service_key
        self._token = None
        self._expires_at = None

    def get_credentials(self) -> dict[str, str]:
        self.refresh_if_needed()
        return {
            'X-User-ID': self.user_id,
            'X-Application-ID': self.app_id,
            'X-Service-Key': self.service_key,
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

    def __init__(self, settings: 'Settings | None' = None):
        self.has_context = has_request_context()
        self._settings = _get_settings_with_fallback(settings)

    def get_credentials(self) -> dict[str, str]:
        if not self.has_context:
            return {}

        user_id = session.get('_user_id', '')
        return {
            'X-User-ID': user_id,
            'X-Application-ID': self._settings.flask.app_id,
            'X-Service-Key': self._settings.auth.internal_service_key,
        }

    def refresh_if_needed(self) -> None:
        # Flask sessions don't need refresh
        pass
