# Resource Clients

Resource clients provide a generic interface for CRUD operations on API endpoints. They work with any Pydantic model and follow consistent patterns for data access.

## Overview

The `ResourceClient` class provides standardized operations for any API resource:

```python
from ichrisbirch.api.client import APIClient
from ichrisbirch.models import TaskModel

# Get a resource client
client = APIClient()
tasks = client.resource('tasks', TaskModel)

# All resources support the same operations
task = tasks.get(123)
all_tasks = tasks.list()
new_task = tasks.create({'title': 'New Task'})
updated_task = tasks.update(123, {'status': 'completed'})
tasks.delete(123)
```

## CRUD Operations

### Get Single Resource

Retrieve a specific resource by ID:

```python
# Get task with ID 123
task = tasks.get(123)
# Returns: TaskModel instance or None

# Get with query parameters
task = tasks.get(123, include_details=True)
```

**HTTP Details:**

- Method: `GET`
- URL: `/{resource_name}/{id}`
- Returns: Pydantic model instance or `None`

### List Resources

Retrieve multiple resources with optional filtering:

```python
# Get all tasks
all_tasks = tasks.list()
# Returns: List[TaskModel]

# Get with filters
active_tasks = tasks.list(status='active', limit=10)
urgent_tasks = tasks.list(priority='high', assigned_to='user123')
```

**HTTP Details:**

- Method: `GET`
- URL: `/{resource_name}`
- Query params: All keyword arguments become query parameters
- Returns: `List[ModelType]`

### Create Resource

Create a new resource:

```python
# Create from dictionary
new_task = tasks.create({
    'title': 'Complete documentation',
    'description': 'Write comprehensive API docs',
    'priority': 'high'
})
# Returns: TaskModel instance

# Create from Pydantic model
task_data = TaskModel(title='Another task', priority='low')
new_task = tasks.create(task_data.model_dump())
```

**HTTP Details:**

- Method: `POST`
- URL: `/{resource_name}`
- Body: JSON data
- Returns: Created model instance

### Update Resource

Update an existing resource:

```python
# Partial update
updated_task = tasks.update(123, {'status': 'completed'})
# Returns: TaskModel instance

# Full update
updated_task = tasks.update(123, {
    'title': 'Updated title',
    'description': 'Updated description',
    'status': 'in_progress'
})
```

**HTTP Details:**

- Method: `PUT`
- URL: `/{resource_name}/{id}`
- Body: JSON data (partial or full)
- Returns: Updated model instance

### Delete Resource

Remove a resource:

```python
# Delete by ID
tasks.delete(123)
# Returns: None (or raises exception on error)

# Delete with confirmation
tasks.delete(123, confirm=True)
```

**HTTP Details:**

- Method: `DELETE`
- URL: `/{resource_name}/{id}`
- Returns: `None`

## Custom Actions

Resources support custom actions beyond CRUD operations:

```python
# POST action with data
result = tasks.action('bulk_complete', {
    'task_ids': [1, 2, 3, 4],
    'completion_note': 'Batch completed'
})

# GET action (no data)
stats = tasks.action('statistics', method='GET')

# Action with query parameters
report = tasks.action('export', method='GET', format='csv', date_range='last_week')
```

**HTTP Details:**

- Method: `POST` (default) or specified method
- URL: `/{resource_name}/{action}`
- Body: JSON data (for POST actions)
- Query params: Additional keyword arguments
- Returns: Action-specific response

## Custom Endpoints

For endpoints that don't follow standard resource patterns:

```python
# Custom endpoint relative to resource
result = tasks.custom_endpoint('GET', '/special-report')

# Custom endpoint with data
result = tasks.custom_endpoint('POST', '/batch-operations', {
    'operation': 'archive',
    'filter': {'status': 'completed'}
})

# Custom endpoint with query parameters
result = tasks.custom_endpoint('GET', '/export', format='json', limit=100)
```

**HTTP Details:**

- Method: As specified
- URL: `/{resource_name}{endpoint}`
- Body: JSON data (if provided)
- Query params: Additional keyword arguments

## Type Safety

Resource clients are fully typed with Pydantic models:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ichrisbirch.models import TaskModel, UserModel

# Type hints work correctly
tasks: ResourceClient[TaskModel] = client.resource('tasks', TaskModel)
users: ResourceClient[UserModel] = client.resource('users', UserModel)

# Return types are properly inferred
task: TaskModel = tasks.get(123)  # Type: TaskModel | None
task_list: List[TaskModel] = tasks.list()  # Type: List[TaskModel]
```

## Error Handling

Resource clients handle errors consistently:

### HTTP Errors

```python
try:
    task = tasks.get(999)  # Non-existent ID
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Task not found")
    else:
        print(f"HTTP error: {e.response.status_code}")
```

### Validation Errors

```python
try:
    new_task = tasks.create({'invalid_field': 'value'})
except httpx.HTTPStatusError as e:
    if e.response.status_code == 422:
        errors = e.response.json()
        print(f"Validation errors: {errors}")
```

### Network Errors

```python
try:
    tasks.list()
except httpx.ConnectError:
    print("Could not connect to API")
except httpx.TimeoutException:
    print("Request timed out")
```

## Usage Patterns

### Resource Factory Pattern

Create resource clients as needed:

```python
def get_user_tasks(user_id: str) -> List[TaskModel]:
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)
        return tasks.list(assigned_to=user_id)
```

### Shared Resource Clients

Reuse resource clients for multiple operations:

```python
def process_tasks():
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)

        # Multiple operations with same client
        pending = tasks.list(status='pending')
        for task in pending:
            result = tasks.action('process', {'task_id': task.id})
            if result['success']:
                tasks.update(task.id, {'status': 'completed'})
```

### Cross-Resource Operations

Work with multiple resource types:

```python
def assign_tasks_to_user(user_id: str, task_ids: List[int]):
    with APIClient() as client:
        users = client.resource('users', UserModel)
        tasks = client.resource('tasks', TaskModel)

        # Verify user exists
        user = users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Assign tasks
        for task_id in task_ids:
            tasks.update(task_id, {'assigned_to': user_id})
```

## Model Integration

Resource clients work seamlessly with Pydantic models:

### Input Validation

```python
# Models validate input data
task_data = TaskModel(
    title="New task",
    priority="high",
    due_date=datetime.now() + timedelta(days=7)
)

# Create using model data
new_task = tasks.create(task_data.model_dump())
```

### Output Parsing

```python
# Responses are parsed into model instances
task = tasks.get(123)

# Access typed attributes
print(task.title)  # String
print(task.created_at)  # datetime
print(task.priority)  # Enum value
```

### Relationship Loading

```python
# Load related data
task = tasks.get(123, include_assignee=True)
print(task.assignee.name)  # Related model data

# Batch operations
completed_tasks = tasks.list(status='completed', include_subtasks=True)
```

## Performance Considerations

1. **Session Reuse**: Use the same APIClient for multiple operations
2. **Batch Operations**: Use custom actions for bulk operations
3. **Filtering**: Use query parameters to reduce data transfer
4. **Pagination**: Handle large result sets appropriately

```python
# Efficient batch processing
with APIClient() as client:
    tasks = client.resource('tasks', TaskModel)

    # Process in batches
    offset = 0
    batch_size = 100

    while True:
        batch = tasks.list(limit=batch_size, offset=offset)
        if not batch:
            break

        # Process batch
        for task in batch:
            process_task(task)

        offset += batch_size
```

## Best Practices

1. **Use Type Hints**: Always specify the Pydantic model type
2. **Handle Errors**: Catch and handle HTTP and network errors appropriately
3. **Session Management**: Use context managers for proper cleanup
4. **Resource Naming**: Use consistent naming that matches API endpoints
5. **Data Validation**: Let Pydantic models handle input validation
6. **Custom Actions**: Use actions for operations that don't fit CRUD patterns
