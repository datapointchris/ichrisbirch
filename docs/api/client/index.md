# API Client Architecture

The ichrisbirch API Client provides a modern, session-based architecture for interacting with the FastAPI backend. This architecture follows industry patterns from libraries like boto3 and Stripe, providing flexible authentication, resource management, and request handling.

## Overview

The API client consists of four main components:

1. **Credential Providers** (`auth.py`) - Pluggable authentication strategies
2. **Session Management** (`session.py`) - Persistent configuration and HTTP client management
3. **Resource Clients** (`resource.py`) - Generic CRUD operations for API resources
4. **Main API Client** (`api.py`) - High-level interface with factory methods

## Quick Start

### Basic Usage

```python
from ichrisbirch.api.client import APIClient

# Context-aware client (automatically detects Flask context)
client = APIClient()

# Get a resource client for tasks
tasks = client.resource('tasks', TaskModel)

# CRUD operations
task = tasks.get(123)
all_tasks = tasks.list()
new_task = tasks.create({'title': 'New Task', 'description': 'Task description'})
updated_task = tasks.update(123, {'status': 'completed'})
tasks.delete(123)

# Custom actions
result = tasks.action('bulk_complete', {'task_ids': [1, 2, 3]})

# Direct API requests
response = client.request('GET', '/custom/endpoint')
```

### Authentication Patterns

```python
from ichrisbirch.api.client import (
    internal_service_client,
    user_client,
    flask_session_client,
    default_client
)

# Internal service authentication
client = internal_service_client('flask-frontend')

# User authentication
client = user_client('user123')

# Flask session authentication
client = flask_session_client()

# Default context-aware authentication
client = default_client()
```

## Architecture Principles

### Session-Based Design

Following the boto3 pattern, the client uses sessions to manage:

- HTTP client lifecycle
- Authentication state
- Base URL and default headers
- Request/response handling

### Pluggable Authentication

Credential providers allow different authentication strategies:

- **InternalServiceProvider**: Service-to-service authentication
- **UserTokenProvider**: User-based token authentication  
- **FlaskSessionProvider**: Flask session-based authentication

### Generic Resource Pattern

Instead of specific factory methods for each resource type, the client uses a generic `resource()` method that works with any Pydantic model:

```python
# Generic pattern (preferred)
tasks = client.resource('tasks', TaskModel)
users = client.resource('users', UserModel)

# Avoids specific factories like:
# tasks = client.tasks()  # Not implemented
# users = client.users()  # Not implemented
```

### Context-Aware Defaults

The client automatically detects context and chooses appropriate authentication:

- Inside Flask request context: Uses Flask session
- Outside Flask context: Uses internal service authentication
- No defensive defaults - fails fast on misconfiguration

## Detailed Documentation

- [Credential Providers](auth.md) - Authentication strategies and implementation
- [Session Management](session.md) - Session lifecycle and configuration
- [Resource Clients](resources.md) - CRUD operations and custom actions
- [Migration Guide](migration.md) - Migrating from QueryAPI to the new client
- [Usage Examples](examples.md) - Common patterns and use cases

## Design Benefits

1. **Industry Standard Pattern**: Follows established patterns from boto3, Stripe, etc.
2. **Flexible Authentication**: Pluggable providers support various auth strategies
3. **Type Safety**: Full Pydantic model integration with proper typing
4. **Resource Agnostic**: Generic client works with any API endpoint
5. **Context Awareness**: Automatically adapts to Flask vs non-Flask environments
6. **Session Management**: Proper HTTP client lifecycle management
7. **Extensible**: Easy to add new credential providers or custom endpoints

## Future Considerations

- **Async Support**: Could add async versions of all methods
- **Caching**: Could add response caching at the session level
- **Retry Logic**: Could add automatic retry with exponential backoff
- **Rate Limiting**: Could add client-side rate limiting
- **Response Streaming**: Could add support for streaming responses
