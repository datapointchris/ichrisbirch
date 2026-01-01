from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any

import httpx

from ichrisbirch.app import utils

from .auth import CredentialProvider
from .auth import FlaskSessionProvider
from .auth import InternalServiceProvider
from .auth import _get_settings_with_fallback

if TYPE_CHECKING:
    from ichrisbirch.config import Settings


class APISession:
    """Session for API client with persistent configuration."""

    def __init__(
        self,
        base_url: str | None = None,
        credential_provider: CredentialProvider | None = None,
        default_headers: dict[str, str] | None = None,
        settings: 'Settings | None' = None,
    ):
        self._settings = _get_settings_with_fallback(settings)
        self.base_url = base_url or self._settings.api_url
        self.credential_provider = credential_provider or self._default_provider()
        self.default_headers = default_headers or {}
        self.client = httpx.Client()

    def _default_provider(self) -> CredentialProvider:
        """Determine default credential provider based on context."""
        with suppress(ImportError):
            from flask import has_request_context

            if has_request_context():
                return FlaskSessionProvider(settings=self._settings)

        return InternalServiceProvider(settings=self._settings)

    def request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make authenticated request."""
        url = utils.url_builder(self.base_url, endpoint)

        self.credential_provider.refresh_if_needed()
        auth_headers = self.credential_provider.get_credentials()

        headers = self.default_headers | auth_headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        response = self.client.request(method, url, headers=headers, **kwargs)
        if response.status_code == 204:
            return None

        response.raise_for_status()
        return response.json()
