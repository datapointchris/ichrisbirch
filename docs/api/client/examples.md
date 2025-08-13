# API Client Usage Examples

This document provides practical examples of using the new API client for common scenarios in the ichrisbirch application.

## Basic Setup

```python
from ichrisbirch.api.client import APIClient, internal_service_client, user_client
from ichrisbirch.models import TaskModel, UserModel, ProjectModel
```

## Flask Web Application Examples

### User Dashboard

```python
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their tasks and projects."""
    # Uses Flask session automatically
    with APIClient() as client:
        tasks_client = client.resource('tasks', TaskModel)
        projects_client = client.resource('projects', ProjectModel)

        # Get user's active tasks
        active_tasks = tasks_client.list(
            assigned_to=session['user_id'],
            status='active',
            limit=10
        )

        # Get user's projects
        projects = projects_client.list(
            owner_id=session['user_id'],
            include_task_counts=True
        )

        return render_template('dashboard.html',
                             tasks=active_tasks,
                             projects=projects)
```

### Task Management

```python
@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as completed."""
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)

        try:
            # Use custom action for completion
            result = tasks.action('complete', {
                'task_id': task_id,
                'completion_note': request.form.get('note', '')
            })

            flash('Task completed successfully', 'success')
            return redirect(url_for('dashboard'))

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                flash('Task not found', 'error')
            elif e.response.status_code == 403:
                flash('Not authorized to complete this task', 'error')
            else:
                flash('Error completing task', 'error')
            return redirect(url_for('dashboard'))
```

### CRUD Operations

```python
@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    """List projects or create new project."""
    with APIClient() as client:
        projects_client = client.resource('projects', ProjectModel)

        if request.method == 'POST':
            # Create new project
            project_data = {
                'name': request.form['name'],
                'description': request.form['description'],
                'owner_id': session['user_id']
            }

            try:
                new_project = projects_client.create(project_data)
                flash(f'Project "{new_project.name}" created', 'success')
                return redirect(url_for('projects'))

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    errors = e.response.json()
                    flash(f'Validation errors: {errors}', 'error')
                else:
                    flash('Error creating project', 'error')

        # List projects
        user_projects = projects_client.list(owner_id=session['user_id'])
        return render_template('projects.html', projects=user_projects)
```

## Background Job Examples

### Data Processing Job

```python
def process_daily_reports():
    """Background job to generate daily reports."""
    # Use internal service authentication
    with internal_service_client('report-processor') as client:
        tasks_client = client.resource('tasks', TaskModel)
        reports_client = client.resource('reports', ReportModel)

        # Get completed tasks from yesterday
        yesterday = datetime.now() - timedelta(days=1)
        completed_tasks = tasks_client.list(
            status='completed',
            completed_after=yesterday.isoformat(),
            limit=1000
        )

        # Generate report
        report_data = {
            'date': yesterday.date().isoformat(),
            'total_completed': len(completed_tasks),
            'completion_rate': calculate_completion_rate(completed_tasks),
            'top_performers': get_top_performers(completed_tasks)
        }

        # Create report
        report = reports_client.create(report_data)
        logger.info(f"Daily report created: {report.id}")

        # Send notifications
        notify_managers(report)
```

### Bulk Operations

```python
def archive_old_tasks():
    """Archive tasks older than 90 days."""
    with internal_service_client('maintenance') as client:
        tasks_client = client.resource('tasks', TaskModel)

        # Find old completed tasks
        cutoff_date = datetime.now() - timedelta(days=90)
        old_tasks = tasks_client.list(
            status='completed',
            completed_before=cutoff_date.isoformat(),
            limit=500  # Process in batches
        )

        if old_tasks:
            # Use bulk action
            task_ids = [task.id for task in old_tasks]
            result = tasks_client.action('bulk_archive', {
                'task_ids': task_ids,
                'archive_reason': 'automatic_cleanup'
            })

            logger.info(f"Archived {result['archived_count']} old tasks")
```

## Service Integration Examples

### External API Integration

```python
class ExternalSyncService:
    """Service to sync data with external API."""

    def __init__(self):
        self.client = internal_service_client('external-sync')
        self.tasks = self.client.resource('tasks', TaskModel)
        self.users = self.client.resource('users', UserModel)

    def sync_user_tasks(self, external_user_id: str):
        """Sync tasks for a user from external system."""
        try:
            # Get external tasks
            external_tasks = self.get_external_tasks(external_user_id)

            # Find corresponding internal user
            user = self.users.list(external_id=external_user_id)[0]

            for ext_task in external_tasks:
                # Check if task already exists
                existing = self.tasks.list(external_id=ext_task['id'])

                task_data = {
                    'title': ext_task['title'],
                    'description': ext_task['description'],
                    'assigned_to': user.id,
                    'external_id': ext_task['id'],
                    'external_updated_at': ext_task['updated_at']
                }

                if existing:
                    # Update existing task
                    self.tasks.update(existing[0].id, task_data)
                else:
                    # Create new task
                    self.tasks.create(task_data)

        except Exception as e:
            logger.error(f"Error syncing tasks for user {external_user_id}: {e}")
            raise

    def close(self):
        self.client.close()
```

### Notification Service

```python
class NotificationService:
    """Service for sending notifications based on API events."""

    def __init__(self):
        self.client = internal_service_client('notification-service')
        self.notifications = self.client.resource('notifications', NotificationModel)
        self.users = self.client.resource('users', UserModel)

    def notify_task_assignment(self, task_id: int, assigned_user_id: str):
        """Send notification when task is assigned."""
        try:
            # Get task details
            tasks = self.client.resource('tasks', TaskModel)
            task = tasks.get(task_id)

            if not task:
                logger.warning(f"Task {task_id} not found for notification")
                return

            # Get user details
            user = self.users.get(assigned_user_id)

            # Create notification
            notification_data = {
                'user_id': assigned_user_id,
                'type': 'task_assignment',
                'title': 'New Task Assigned',
                'message': f'You have been assigned task: {task.title}',
                'related_object_type': 'task',
                'related_object_id': task_id,
                'priority': task.priority
            }

            notification = self.notifications.create(notification_data)

            # Send via email/SMS if needed
            if user.notification_preferences.get('email_enabled'):
                self.send_email_notification(user, notification)

        except Exception as e:
            logger.error(f"Error sending task assignment notification: {e}")

    def close(self):
        self.client.close()
```

## Testing Examples

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import Mock, patch
from ichrisbirch.api.client import APIClient
from ichrisbirch.api.client.auth import MockCredentialProvider

class TestTaskService:

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client for testing."""
        provider = MockCredentialProvider({"Authorization": "Bearer test-token"})
        return APIClient(
            base_url="http://test-api:8000",
            credential_provider=provider
        )

    def test_get_user_tasks(self, mock_api_client):
        """Test getting user tasks."""
        # Mock the HTTP response
        with patch.object(mock_api_client.session.client, 'request') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = [
                {'id': 1, 'title': 'Test Task', 'assigned_to': 'user123'},
                {'id': 2, 'title': 'Another Task', 'assigned_to': 'user123'}
            ]
            mock_request.return_value = mock_response

            # Test the service
            tasks = mock_api_client.resource('tasks', TaskModel)
            user_tasks = tasks.list(assigned_to='user123')

            # Verify the request
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert kwargs['method'] == 'GET'
            assert 'tasks' in kwargs['url']
            assert kwargs['params'] == {'assigned_to': 'user123'}
```

### Integration Testing

```python
@pytest.mark.integration
class TestAPIClientIntegration:
    """Integration tests with actual API."""

    @pytest.fixture
    def api_client(self):
        """Real API client for integration tests."""
        return APIClient(base_url=os.environ['TEST_API_URL'])

    def test_crud_operations(self, api_client):
        """Test full CRUD cycle."""
        with api_client:
            tasks = api_client.resource('tasks', TaskModel)

            # Create
            task_data = {
                'title': 'Integration Test Task',
                'description': 'Created by integration test',
                'priority': 'low'
            }
            created_task = tasks.create(task_data)
            assert created_task.id is not None
            assert created_task.title == task_data['title']

            # Read
            fetched_task = tasks.get(created_task.id)
            assert fetched_task.title == created_task.title

            # Update
            updated_data = {'status': 'in_progress'}
            updated_task = tasks.update(created_task.id, updated_data)
            assert updated_task.status == 'in_progress'

            # Delete
            tasks.delete(created_task.id)

            # Verify deletion
            deleted_task = tasks.get(created_task.id)
            assert deleted_task is None
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
def robust_task_processing(task_id: int):
    """Process task with comprehensive error handling."""
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)

        try:
            # Get task
            task = tasks.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return {'success': False, 'error': 'Task not found'}

            # Process task
            result = tasks.action('process', {'task_id': task_id})

            return {'success': True, 'result': result}

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = f"Task {task_id} not found"
            elif e.response.status_code == 422:
                validation_errors = e.response.json()
                error_msg = f"Validation errors: {validation_errors}"
            elif e.response.status_code == 403:
                error_msg = "Not authorized to process this task"
            else:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"

            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        except httpx.ConnectError:
            error_msg = "Could not connect to API server"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        except httpx.TimeoutException:
            error_msg = "Request timed out"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            return {'success': False, 'error': error_msg}
```

### Retry Logic

```python
import time
from typing import Callable, Any

def with_retry(func: Callable, max_attempts: int = 3, delay: float = 1.0) -> Any:
    """Execute function with retry logic."""
    for attempt in range(max_attempts):
        try:
            return func()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt == max_attempts - 1:
                raise e

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

def get_tasks_with_retry():
    """Get tasks with automatic retry."""
    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)

        return with_retry(lambda: tasks.list(status='active'))
```

## Performance Optimization

### Connection Reuse

```python
class TaskProcessor:
    """Long-running task processor that reuses connections."""

    def __init__(self):
        self.client = internal_service_client('task-processor')
        self.tasks = self.client.resource('tasks', TaskModel)
        self.notifications = self.client.resource('notifications', NotificationModel)

    def process_batch(self, batch_size: int = 50):
        """Process tasks in batches."""
        offset = 0

        while True:
            # Get batch of pending tasks
            pending_tasks = self.tasks.list(
                status='pending',
                limit=batch_size,
                offset=offset
            )

            if not pending_tasks:
                break

            # Process each task
            for task in pending_tasks:
                try:
                    self.process_single_task(task)
                except Exception as e:
                    logger.error(f"Error processing task {task.id}: {e}")

            offset += batch_size

    def process_single_task(self, task: TaskModel):
        """Process a single task."""
        # Update status
        self.tasks.update(task.id, {'status': 'processing'})

        # Do processing work
        result = self.do_work(task)

        # Update with result
        self.tasks.update(task.id, {
            'status': 'completed',
            'result': result
        })

        # Send notification
        self.notifications.create({
            'user_id': task.assigned_to,
            'type': 'task_completed',
            'message': f'Task "{task.title}" completed'
        })

    def close(self):
        """Clean up resources."""
        self.client.close()
```

### Pagination Handling

```python
def get_all_tasks() -> List[TaskModel]:
    """Get all tasks using pagination."""
    all_tasks = []

    with APIClient() as client:
        tasks = client.resource('tasks', TaskModel)

        page_size = 100
        offset = 0

        while True:
            batch = tasks.list(limit=page_size, offset=offset)
            if not batch:
                break

            all_tasks.extend(batch)
            offset += page_size

            # Avoid infinite loops
            if len(batch) < page_size:
                break

    return all_tasks
```

These examples demonstrate practical usage patterns for the new API client in various scenarios throughout the ichrisbirch application.
