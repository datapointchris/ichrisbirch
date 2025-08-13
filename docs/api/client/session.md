# Session Management

The `APISession` class manages HTTP client lifecycle, authentication state, and request/response handling. It provides a persistent, configured connection to the API server.

## Core Concepts

### Session Lifecycle

Sessions manage the underlying HTTP client and provide consistent configuration across multiple requests:

```python
from ichrisbirch.api.client import APIClient

# Session is created automatically
client = APIClient()

# Session is reused for all requests
tasks = client.resource('tasks', TaskModel)
users = client.resource('users', UserModel)

# Properly close when done
client.close()

# Or use context manager
with APIClient() as client:
    tasks = client.resource('tasks', TaskModel)
    # Session automatically closed
```

### Configuration

Sessions are configured with:

- **Base URL**: Default API server endpoint
- **Credential Provider**: Authentication strategy
- **Default Headers**: Headers added to all requests
- **HTTP Client**: Persistent connection pool

```python
# Custom configuration
client = APIClient(
    base_url="https://api.example.com",
    credential_provider=custom_provider,
    default_headers={"User-Agent": "MyApp/1.0"}
)
```

## Default Behavior

### Automatic Base URL Detection

When no base URL is provided, the session uses `settings.api_url`:

```python
# Uses settings.api_url automatically
client = APIClient()

# Explicit base URL override
client = APIClient(base_url="https://custom-api.com")
```

### Context-Aware Authentication

Sessions automatically select appropriate authentication based on context:

```python
def _default_provider(self) -> CredentialProvider:
    """Select appropriate provider based on context."""
    if has_request_context():
        return FlaskSessionProvider()
    else:
        return InternalServiceProvider()
```

**In Flask Request Context:**

- Uses `FlaskSessionProvider`
- Extracts user credentials from Flask session
- Suitable for web requests

**Outside Flask Context:**

- Uses `InternalServiceProvider`
- Uses service-to-service authentication
- Suitable for background jobs, scripts

## Request Handling

### URL Building

Sessions handle URL construction using the existing `utils.url_builder()` function:

```python
# Input: endpoint = "/tasks/123"
# Base URL: "https://api.example.com"
# Result: "https://api.example.com/tasks/123/"

url = utils.url_builder(self.base_url, endpoint)
```

This preserves the existing URL building patterns and ensures consistent path handling.

### Header Management

Sessions merge headers from multiple sources:

1. **Default headers** (from session configuration)
2. **Authentication headers** (from credential provider)
3. **Request-specific headers** (from method call)

```python
# Session default headers
session = APISession(default_headers={"User-Agent": "MyApp/1.0"})

# Credential provider headers
# {"Authorization": "Bearer token"}

# Request headers
session.request("GET", "/tasks", headers={"Accept": "application/json"})

# Final merged headers:
# {
#   "User-Agent": "MyApp/1.0",
#   "Authorization": "Bearer token",
#   "Accept": "application/json"
# }
```

### HTTP Client Management

Sessions use httpx for HTTP requests with these features:

- **Connection pooling**: Reuses connections for better performance
- **Timeout handling**: Configurable request timeouts
- **Error handling**: Proper HTTP error responses
- **JSON serialization**: Automatic JSON encoding/decoding

```python
# The session manages httpx.Client lifecycle
class APISession:
    def __init__(self, ...):
        self.client = httpx.Client()

    def request(self, method: str, endpoint: str, **kwargs) -> Any:
        response = self.client.request(method, url, **merged_kwargs)
        return response.json()

    def close(self):
        self.client.close()
```

## Usage Patterns

### Long-Running Sessions

For applications that make many API calls, reuse the session:

```python
# Good: Reuse session
client = APIClient()
for item in items:
    result = client.resource('tasks', TaskModel).create(item)
client.close()

# Better: Use context manager
with APIClient() as client:
    tasks = client.resource('tasks', TaskModel)
    for item in items:
        result = tasks.create(item)
```

### Short-Lived Sessions

For one-off requests, sessions can be created and discarded:

```python
# Quick operations
def get_user(user_id: str) -> UserModel:
    with APIClient() as client:
        return client.resource('users', UserModel).get(user_id)
```

### Custom Authentication

Override default authentication for specific needs:

```python
# Service authentication
client = APIClient(credential_provider=InternalServiceProvider("background-job"))

# User authentication  
client = APIClient(credential_provider=UserTokenProvider("user123"))

# Custom authentication
client = APIClient(credential_provider=CustomProvider(...))
```

## Configuration Examples

### Development Environment

```python
# Local development with debug headers
client = APIClient(
    base_url="http://localhost:8000",
    default_headers={
        "X-Debug": "true",
        "User-Agent": "Development-Client"
    }
)
```

### Production Environment

```python
# Production with proper timeouts and headers
client = APIClient(
    default_headers={
        "User-Agent": "ichrisbirch-frontend/1.0",
        "X-Request-Source": "flask-app"
    }
)
```

### Testing Environment

```python
# Testing with mock authentication
mock_provider = MockCredentialProvider({"Authorization": "Bearer test-token"})
client = APIClient(
    base_url="http://test-api:8000",
    credential_provider=mock_provider
)
```

## Error Handling

Sessions handle errors at multiple levels:

### HTTP Errors

```python
try:
    response = session.request("GET", "/invalid-endpoint")
except httpx.HTTPStatusError as e:
    print(f"HTTP {e.response.status_code}: {e.response.text}")
```

### Connection Errors

```python
try:
    response = session.request("GET", "/tasks")
except httpx.ConnectError:
    print("Could not connect to API server")
```

### Authentication Errors

```python
# Credential provider errors
if not session.credential_provider.is_available():
    raise AuthenticationError("No credentials available")
```

## Performance Considerations

1. **Connection Reuse**: Sessions maintain persistent connections
2. **Request Pooling**: httpx handles connection pooling automatically
3. **Memory Management**: Close sessions when done to free resources
4. **Concurrent Requests**: Sessions are not thread-safe; use separate sessions per thread

## Best Practices

1. **Use Context Managers**: Always use `with APIClient() as client:` when possible
2. **Session Reuse**: Don't create new clients for each request
3. **Proper Cleanup**: Call `close()` or use context managers
4. **Error Handling**: Handle both HTTP and connection errors
5. **Configuration**: Set base_url and headers at session level, not per request
