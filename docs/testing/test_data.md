# Test Data Management

This document explains how test data is organized, managed, and used in the ichrisbirch project testing infrastructure.

## Test Data Structure

The test data is organized into modules within the `tests.test_data` package, with each module responsible for providing data for a specific model or feature:

Each module typically contains:

- A `BASE_DATA` constant containing instances of the relevant model
- Additional test data constants for specific test scenarios
- Helper functions for creating or modifying test data

## Data Format

Test data is defined using direct model instantiation:

```python
from datetime import datetime
from ichrisbirch.models import Event

BASE_DATA: list[Event] = [
    Event(
        name='Event 1',
        date=datetime(2022, 10, 1, 10, 0).isoformat(),
        venue='Venue 1',
        url='https://example.com/event1',
        cost=10.0,
        attending=True,
        notes='Notes for Event 1',
    ),
    # More events...
]
```

## Test Data Registry

The `get_test_data()` function in `tests/utils/database.py` provides a registry of all available test datasets:

```python
def get_test_data() -> Dict[str, Dict[str, Any]]:
    return {
        'articles': {'model': models.Article, 'data': tests.test_data.articles.BASE_DATA},
        'autotasks': {'model': models.AutoTask, 'data': tests.test_data.autotasks.BASE_DATA},
        'books': {'model': models.Book, 'data': tests.test_data.books.BASE_DATA},
        # More datasets...
    }
```

This registry maps dataset names to their corresponding models and data collections.

## Data Management Functions

### Inserting Test Data

The `insert_test_data()` function inserts specific datasets into the database:

```python
def insert_test_data(*datasets):
    """Insert testing data for specific datasets.

    Args:
        *datasets: Names of datasets to insert (e.g., 'tasks', 'users')
    """
    test_data = get_test_data()
    selected_datasets = [deepcopy(test_data[key]['data']) for key in datasets]

    with TestSessionLocal() as session:
        for data in selected_datasets:
            session.add_all(data)
        session.commit()
```

### Deleting Test Data

The `delete_test_data()` function removes specific datasets from the database:

```python
def delete_test_data(*datasets):
    """Delete test data except login users.

    Args:
        *datasets: Names of datasets to delete (e.g., 'tasks', 'users')
    """
    # Implementation details...
```

This function includes special handling for user data to preserve login users.

## Using Test Data in Fixtures

Test data is typically inserted and deleted using fixtures:

```python
@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('tasks')
    yield
    delete_test_data('tasks')
```

This pattern ensures that:

1. The required test data is available before tests run
2. Test data is cleaned up after tests complete
3. Tests start with a consistent, known state

## Multiple Dataset Dependencies

For tests requiring multiple related datasets, you can insert them together:

```python
@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('habitcategories', 'habits', 'habitscompleted')
    yield
    delete_test_data('habits', 'habitscompleted', 'habitcategories')
```

Note that when deleting related datasets, you must consider foreign key relationships and delete in the correct order.

## Login Users

Special handling exists for test login users:

```python
def get_test_login_users() -> List[Dict[str, Any]]:
    """Return a list of test users for login testing."""
    settings = get_test_settings()

    return [
        {
            'name': 'Test User to be Sacrificed for Delete Test',
            'email': 'sacrifice@testgods.com',
            'password': 'repentance',
        },
        {
            'name': 'Test Login Regular User',
            'email': 'testloginregular@testuser.com',
            'password': 'regularpassword',
        },
        {
            'name': 'Test Login Admin User',
            'email': 'testloginadmin@testadmin.com',
            'password': 'adminpassword',
            'is_admin': True,
        },
        {
            'name': settings.users.service_account_user_name,
            'email': settings.users.service_account_user_email,
            'password': settings.users.service_account_user_password,
        },
    ]
```

These users are:

1. Inserted at the module level via the `insert_users_for_login` fixture
2. Preserved when deleting user test data
3. Available for authentication in tests

## Best Practices for Test Data

1. **Keep test data minimal**: Include only the fields necessary for tests
2. **Use realistic values**: Test data should represent real-world scenarios
3. **Avoid dependencies**: When possible, make test data self-contained
4. **Document relationships**: When test data has dependencies, document them
5. **Consider database constraints**: Ensure test data satisfies database constraints
6. **Handle cleanup**: Always clean up test data after tests
7. **Use consistent IDs**: When IDs matter, use explicit, consistent IDs
8. **Reset sequences**: Reset ID sequences after deleting test data
