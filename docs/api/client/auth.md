# Credential Providers

Credential providers are pluggable authentication strategies that supply credentials for API requests. They follow a simple interface and can be easily extended for different authentication scenarios.

## CredentialProvider Interface

All credential providers implement the abstract `CredentialProvider` class:

```python
class CredentialProvider(ABC):
    """Abstract base for credential providers."""

    @abstractmethod
    def get_credentials(self) -> Dict[str, str]:
        """Return headers to be added to requests."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if credentials are available."""
        pass
```

## Built-in Providers

### InternalServiceProvider

Used for service-to-service authentication within the ichrisbirch ecosystem.

```python
from ichrisbirch.api.client.auth import InternalServiceProvider

provider = InternalServiceProvider(service_name="flask-frontend")
credentials = provider.get_credentials()
# Returns: {"Authorization": "Service flask-frontend <service_key>"}
```

**Use Cases:**

- Flask app calling FastAPI endpoints
- Background jobs accessing the API
- Internal microservice communication

**Configuration:**

- Requires `AUTH_INTERNAL_SERVICE_KEY` environment variable
- Service name identifies the calling service

### UserTokenProvider

Used for user-based authentication with JWT tokens or similar.

```python
from ichrisbirch.api.client.auth import UserTokenProvider

provider = UserTokenProvider(user_id="user123", app_id="web-app")
credentials = provider.get_credentials()
# Returns: {"Authorization": "Bearer <user_token>"}
```

**Use Cases:**

- API calls on behalf of a specific user
- Background tasks with user context
- Service calls that need user permissions

**Implementation Notes:**

- Token retrieval should be implemented based on your token storage
- Could integrate with JWT libraries, database lookups, or external auth services
- May include token refresh logic

### FlaskSessionProvider

Uses Flask session data for authentication in web request contexts.

```python
from ichrisbirch.api.client.auth import FlaskSessionProvider

provider = FlaskSessionProvider()
credentials = provider.get_credentials()
# Returns: {"Authorization": "User <user_id>", "X-App-ID": "<app_id>"}
```

**Use Cases:**

- Web requests where user is already authenticated
- Form submissions and AJAX calls
- Any Flask route that needs to call the API

**Behavior:**

- Only available within Flask request context
- Extracts user_id and app_id from session
- Returns empty dict if session data is missing

## Default Provider Selection

The `APISession` automatically selects an appropriate provider when none is explicitly provided:

```python
def _default_provider(self) -> CredentialProvider:
    """Select appropriate provider based on context."""
    if has_request_context():
        return FlaskSessionProvider()
    else:
        return InternalServiceProvider()
```

This provides context-aware authentication:

- **In Flask requests**: Uses session-based auth
- **Outside Flask**: Uses internal service auth

## Custom Providers

You can create custom credential providers for specific authentication needs:

```python
class APIKeyProvider(CredentialProvider):
    """API key based authentication."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_credentials(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key}

    def is_available(self) -> bool:
        return bool(self.api_key)

# Usage
provider = APIKeyProvider("your-api-key")
client = APIClient(credential_provider=provider)
```

## Provider Selection Guide

| Context | Recommended Provider | Use Case |
|---------|---------------------|----------|
| Flask request with user session | `FlaskSessionProvider` | Web app user actions |
| Flask request without session | `InternalServiceProvider` | Internal API calls |
| Background job with user context | `UserTokenProvider` | User-specific tasks |
| Background job system task | `InternalServiceProvider` | System maintenance |
| External script/tool | `APIKeyProvider` (custom) | CLI tools, scripts |
| Testing | `InternalServiceProvider` | Test automation |

## Error Handling

Credential providers follow a fail-fast approach:

- `is_available()` returns `False` when credentials cannot be obtained
- `get_credentials()` may raise exceptions for configuration errors
- No defensive defaults - missing configuration should fail clearly

This ensures authentication problems are detected early rather than silently failing with unclear errors.

## Security Considerations

1. **Service Keys**: Store in environment variables, not code
2. **User Tokens**: Implement secure token storage and refresh logic
3. **Session Security**: Ensure Flask sessions are properly secured
4. **Credential Rotation**: Design providers to support key/token rotation
5. **Logging**: Avoid logging credential values in plaintext

## Testing

Mock credential providers for testing:

```python
class MockCredentialProvider(CredentialProvider):
    def __init__(self, credentials: Dict[str, str]):
        self._credentials = credentials

    def get_credentials(self) -> Dict[str, str]:
        return self._credentials

    def is_available(self) -> bool:
        return True

# Test usage
mock_provider = MockCredentialProvider({"Authorization": "Bearer test-token"})
client = APIClient(credential_provider=mock_provider)
```
