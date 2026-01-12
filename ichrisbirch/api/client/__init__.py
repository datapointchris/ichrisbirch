"""
ichrisbirch API Client

A modern, session-based API client for the ichrisbirch FastAPI backend.
Follows industry patterns from boto3 and Stripe with pluggable authentication,
generic resource clients, and context-aware defaults.

Quick Start:
    from ichrisbirch.api.client import default_client

    with default_client() as client:
        tasks = client.resource('tasks', TaskModel)
        task = tasks.get(123)
        new_task = tasks.create({'title': 'New Task'})

Authentication:
    - default_client(): Context-aware (Flask session or internal service)
    - internal_service_client(): Service-to-service authentication
    - user_client(): User token authentication
    - flask_session_client(): Flask session authentication

Error Handling:
    The client raises exceptions on errors (never silently returns None/[]):
    - APIClientError: Base class for all API client errors
    - APIHTTPError: HTTP 4xx/5xx responses
    - APIConnectionError: Network/connection failures
    - APIParseError: Response parsing failures
"""

from .api import APIClient
from .api import default_client
from .api import flask_session_client
from .api import internal_service_client
from .api import user_client
from .auth import CredentialProvider
from .auth import FlaskSessionProvider
from .auth import InternalServiceProvider
from .auth import UserTokenProvider
from .exceptions import APIClientError
from .exceptions import APIConnectionError
from .exceptions import APIHTTPError
from .exceptions import APIParseError
from .resource import ResourceClient
from .session import APISession

__all__ = [
    # Main client classes
    'APIClient',
    'APISession',
    'ResourceClient',
    # Factory functions
    'default_client',
    'internal_service_client',
    'user_client',
    'flask_session_client',
    # Authentication providers
    'CredentialProvider',
    'InternalServiceProvider',
    'UserTokenProvider',
    'FlaskSessionProvider',
    # Exceptions
    'APIClientError',
    'APIHTTPError',
    'APIConnectionError',
    'APIParseError',
]
