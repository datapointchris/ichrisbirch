# Migration Guide: QueryAPI to API Client

This guide helps you migrate from the existing `QueryAPI` class to the new session-based API client architecture.

## Overview of Changes

The new API client provides:

- **Session-based architecture** following industry patterns (boto3, Stripe)
- **Pluggable authentication** with credential providers
- **Generic resource pattern** instead of specific methods
- **Better type safety** with full Pydantic integration
- **Context-aware defaults** for Flask vs non-Flask environments

## Migration Strategy

### Phase 1: Coexistence

Both systems can coexist during migration:

```python
# Old QueryAPI (still available)
from ichrisbirch.app.query_api import QueryAPI
query_api = QueryAPI(use_internal_auth=True)

# New API Client
from ichrisbirch.api.client import APIClient
client = APIClient()
```

### Phase 2: Gradual Migration

Migrate one endpoint at a time:

```python
# Before: QueryAPI
def get_tasks():
    query_api = QueryAPI()
    return query_api.get_generic("tasks")

# After: API Client
def get_tasks():
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)
        return tasks.list()
```

### Phase 3: Complete Migration

Remove QueryAPI usage and update all code to use the new client.

## Common Migration Patterns

### Basic GET Requests

**Before (QueryAPI):**

```python
query_api = QueryAPI()
tasks = query_api.get_generic("tasks")
task = query_api.get_generic("tasks", resource_id=123)
```

**After (API Client):**

```python
with APIClient() as client:
    tasks_client = client.resource('tasks', TaskModel)
    tasks = tasks_client.list()
    task = tasks_client.get(123)
```

### POST Actions

**Before (QueryAPI):**

```python
query_api = QueryAPI()
result = query_api.post_action("tasks/bulk_complete", {
    'task_ids': [1, 2, 3]
})
```

**After (API Client):**

```python
with APIClient() as client:
    tasks = client.resource('tasks', TaskModel)
    result = tasks.action('bulk_complete', {
        'task_ids': [1, 2, 3]
    })
```

### Custom Endpoints

**Before (QueryAPI):**

```python
query_api = QueryAPI()
data = query_api.get_generic("custom/endpoint")
result = query_api.post_action("custom/action", {'data': 'value'})
```

**After (API Client):**

```python
with APIClient() as client:
    # Direct requests for truly custom endpoints
    data = client.request('GET', '/custom/endpoint')
    result = client.request('POST', '/custom/action', json={'data': 'value'})

    # Or if it belongs to a resource
    resource = client.resource('custom', CustomModel)
    data = resource.custom_endpoint('GET', '/endpoint')
    result = resource.custom_endpoint('POST', '/action', {'data': 'value'})
```

### Authentication Patterns

**Before (QueryAPI):**

```python
# Internal service
query_api = QueryAPI(use_internal_auth=True)

# User context (automatic)
query_api = QueryAPI()  # Uses Flask session
```

**After (API Client):**

```python
# Internal service
from ichrisbirch.api.client import internal_service_client
client = internal_service_client()

# User context (automatic)
from ichrisbirch.api.client import default_client
client = default_client()  # Context-aware

# Or explicit Flask session
from ichrisbirch.api.client import flask_session_client
client = flask_session_client()
```

## Specific QueryAPI Method Migrations

### get_generic()

**QueryAPI Pattern:**

```python
def get_generic(self, endpoint: str, resource_id: int = None, **params) -> Union[List[Dict], Dict, None]:
    # Internal implementation
    return response_data
```

**API Client Equivalent:**

```python
# For resource operations
tasks = client.resource('tasks', TaskModel)
all_tasks = tasks.list(**params)  # GET /tasks
single_task = tasks.get(resource_id, **params)  # GET /tasks/{id}

# For custom endpoints
response = client.request('GET', f'/{endpoint}', params=params)
```

### post_action()

**QueryAPI Pattern:**

```python
def post_action(self, endpoint: str, data: Dict) -> Dict:
    # Internal implementation
    return response_data
```

**API Client Equivalent:**

```python
# For resource actions
resource = client.resource('tasks', TaskModel)
result = resource.action('action_name', data)

# For custom endpoints
result = client.request('POST', f'/{endpoint}', json=data)
```

### Internal Authentication

**QueryAPI Pattern:**

```python
query_api = QueryAPI(use_internal_auth=True)
```

**API Client Equivalent:**

```python
from ichrisbirch.api.client import internal_service_client
client = internal_service_client("flask-frontend")
```

## File-by-File Migration Examples

### Flask Route Migration

**Before:**

```python
@app.route('/tasks')
def get_tasks():
    query_api = QueryAPI()
    tasks = query_api.get_generic("tasks", status="active")
    return render_template('tasks.html', tasks=tasks)
```

**After:**

```python
@app.route('/tasks')
def get_tasks():
    with APIClient() as client:
        tasks_client = client.resource('tasks', TaskModel)
        tasks = tasks_client.list(status="active")
        return render_template('tasks.html', tasks=tasks)
```

### Background Job Migration

**Before:**

```python
def process_pending_tasks():
    query_api = QueryAPI(use_internal_auth=True)
    pending = query_api.get_generic("tasks", status="pending")

    for task in pending:
        result = query_api.post_action(f"tasks/{task['id']}/process", {})
        if result['success']:
            query_api.post_action(f"tasks/{task['id']}/complete", {})
```

**After:**

```python
def process_pending_tasks():
    with internal_service_client("background-processor") as client:
        tasks = client.resource('tasks', TaskModel)
        pending = tasks.list(status="pending")

        for task in pending:
            result = tasks.action('process', task_id=task.id)
            if result['success']:
                tasks.action('complete', task_id=task.id)
```

### Service Class Migration

**Before:**

```python
class TaskService:
    def __init__(self):
        self.query_api = QueryAPI()

    def get_user_tasks(self, user_id: str):
        return self.query_api.get_generic("tasks", assigned_to=user_id)

    def complete_task(self, task_id: int):
        return self.query_api.post_action(f"tasks/{task_id}/complete", {})
```

**After:**

```python
class TaskService:
    def __init__(self):
        self.client = APIClient()
        self.tasks = self.client.resource('tasks', TaskModel)

    def get_user_tasks(self, user_id: str):
        return self.tasks.list(assigned_to=user_id)

    def complete_task(self, task_id: int):
        return self.tasks.action('complete', task_id=task_id)

    def close(self):
        self.client.close()
```

## Testing Migration

### Mock QueryAPI

**Before:**

```python
def test_get_tasks(monkeypatch):
    def mock_get_generic(endpoint, **params):
        return [{'id': 1, 'title': 'Test Task'}]

    monkeypatch.setattr(QueryAPI, 'get_generic', mock_get_generic)
    # Test code...
```

**After:**

```python
def test_get_tasks():
    mock_provider = MockCredentialProvider({"Authorization": "Bearer test"})
    with APIClient(credential_provider=mock_provider) as client:
        # Use actual client with mock auth
        pass

# Or mock at HTTP level
@responses.activate  
def test_get_tasks():
    responses.add(responses.GET,
                 "http://api.test/tasks",
                 json=[{'id': 1, 'title': 'Test Task'}])

    with APIClient(base_url="http://api.test") as client:
        tasks = client.resource('tasks', TaskModel)
        result = tasks.list()
```

## Breaking Changes

### Method Names

| QueryAPI | API Client |
|----------|------------|
| `get_generic(endpoint)` | `resource(name, model).list()` |
| `get_generic(endpoint, resource_id=123)` | `resource(name, model).get(123)` |
| `post_action(endpoint, data)` | `resource(name, model).action(name, data)` |
| Custom methods | `request(method, endpoint, **kwargs)` |

### Return Types

- **QueryAPI**: Returns raw dictionaries and lists
- **API Client**: Returns Pydantic model instances

### Authentication

- **QueryAPI**: Boolean flag `use_internal_auth`
- **API Client**: Pluggable credential providers

### Configuration

- **QueryAPI**: Hardcoded settings and Flask coupling
- **API Client**: Configurable sessions with explicit dependencies

## Rollback Strategy

If issues arise during migration:

1. **Keep QueryAPI Available**: Don't remove QueryAPI until migration is complete
2. **Incremental Rollback**: Roll back one endpoint at a time if needed
3. **Feature Flags**: Use feature flags to toggle between old and new implementations

```python
def get_tasks():
    if settings.use_new_api_client:
        with APIClient() as client:
            return client.resource('tasks', TaskModel).list()
    else:
        query_api = QueryAPI()
        return query_api.get_generic("tasks")
```

## Migration Checklist

### Before Migration

- [ ] Understand current QueryAPI usage patterns
- [ ] Identify all endpoints and authentication requirements
- [ ] Set up Pydantic models for all resources
- [ ] Plan migration order (start with low-risk endpoints)

### During Migration

- [ ] Migrate one endpoint at a time
- [ ] Test each migration thoroughly
- [ ] Update all related tests
- [ ] Update documentation and examples
- [ ] Monitor for performance issues

### After Migration

- [ ] Remove QueryAPI imports and usage
- [ ] Clean up old authentication code
- [ ] Update CI/CD pipelines
- [ ] Train team on new patterns
- [ ] Update development guidelines

## Common Pitfalls

1. **Session Management**: Remember to close clients or use context managers
2. **Authentication Context**: Understand when Flask session vs internal auth is used
3. **Type Safety**: Use proper Pydantic models for type checking
4. **Error Handling**: New client may raise different exceptions
5. **URL Building**: New client uses existing `utils.url_builder()` patterns

## Support

For migration assistance:

1. **Documentation**: Reference the full API client documentation
2. **Examples**: See `examples.md` for common patterns
3. **Testing**: Use mock credential providers for unit tests
4. **Performance**: Monitor response times and connection usage
