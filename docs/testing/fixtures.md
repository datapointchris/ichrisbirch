# Test Fixtures

This document details the test fixtures available in the ichrisbirch project's testing infrastructure. These fixtures provide standardized ways to set up test prerequisites and resources.

## Fixture Scopes

The project uses fixtures at different scopes to optimize test execution:

![Test Fixture Hierarchy](../images/generated/fixtures_diagram.svg)

## Session Fixtures

Session fixtures run once per test session and are available throughout the testing process:

### `setup_test_environment`

- **Scope**: Session
- **Autouse**: Yes
- **Description**: Sets up the entire test environment including Docker containers and server processes
- **Implementation**: Defined in `conftest.py` and calls the `TestEnvironment.setup()` method

```python file=tests/conftest.py element=setup_test_environment label="setup_test_environment"
@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    logger.warning('')
    logger.warning(f'{"=" * 30}>  STARTING TESTING  <{"=" * 30}')
    logger.warning('')

    with DockerComposeTestEnvironment(test_settings, create_session) as test_env:
        logger.info('Docker Compose test environment is ready')
        yield test_env

    logger.warning('')
    logger.warning(f'{"=" * 30}>  TESTING FINISHED  <{"=" * 30}')
    logger.warning('')
```

## Module Fixtures

Module fixtures run once per test module:

### `create_drop_tables`

- **Scope**: Module
- **Description**: Creates tables in the test database at the beginning of a test module and drops them when the module completes
- **Implementation**: Uses SQLAlchemy's metadata to create and drop tables

### `insert_users_for_login`

- **Scope**: Module
- **Autouse**: Yes
- **Description**: Inserts test users needed for login authentication
- **Dependencies**: `create_drop_tables`
- **Implementation**: Inserts predefined test users from `get_test_login_users()`

### Test Client Fixtures (Module Scope)

Various test client fixtures provide access to the API and App with different authentication levels:

| Fixture Name | Description | Authentication |
|--------------|-------------|----------------|
| `test_api` | Basic API test client | None |
| `test_api_logged_in` | API client with regular user authentication | Regular user |
| `test_api_logged_in_admin` | API client with admin authentication | Admin user |
| `test_app` | Basic App test client | None |
| `test_app_logged_in` | App client with regular user authentication | Regular user |
| `test_app_logged_in_admin` | App client with admin authentication | Admin user |

### `test_jobstore`

- **Scope**: Module
- **Description**: Provides access to the APScheduler job store for testing scheduler functionality
- **Implementation**: Calls `get_jobstore()` with test settings

## Function Fixtures

Function fixtures run once per test function:

### Test Client Fixtures (Function Scope)

These fixtures are function-scoped versions of the module-scoped test client fixtures:

| Fixture Name                        | Description                                       | Authentication |
| ----------------------------------- | ------------------------------------------------- | -------------- |
| `test_api_function`                 | Function-scoped basic API client                  | None           |
| `test_api_logged_in_function`       | Function-scoped API client with regular user auth | Regular user   |
| `test_api_logged_in_admin_function` | Function-scoped API client with admin auth        | Admin user     |
| `test_app_function`                 | Function-scoped basic App client                  | None           |
| `test_app_logged_in_function`       | Function-scoped App client with regular user auth | Regular user   |
| `test_app_logged_in_admin_function` | Function-scoped App client with admin auth        | Admin user     |

## Test Data Fixtures

Test data fixtures handle the insertion and cleanup of test data:

### `insert_testing_data`

- **Autouse**: Often set to `True` in individual test modules
- **Description**: Inserts specific test datasets and cleans them up after tests
- **Implementation**: Uses `insert_test_data()` and `delete_test_data()` functions
- **Example**:

k

```python file=tests/utils/database.py element=insert_test_data label="insert_testing_data"
def insert_test_data(*datasets):
    test_data = get_test_data()
    selected_datasets = [deepcopy(test_data[key]['data']) for key in datasets]

    with create_session(test_settings) as session:
        for data in selected_datasets:
            session.add_all(data)
        session.commit()
    for d in datasets:
        logger.info(f'inserted testing dataset: {d}')
```

### `insert_jobs_in_test_scheduler`

- **Description**: Adds test jobs to the scheduler for testing scheduler functionality
- **Implementation**: Creates a test scheduler and adds jobs from test data

### User Fixtures

- **`test_user`**: Provides a test user instance
- **`test_admin_user`**: Provides a test admin user instance

## Using Fixtures in Tests

To use fixtures in tests, you can either:

1. **Parameter Injection**: Add the fixture name as a parameter to your test function

   ```python
   def test_api_endpoint(test_api_logged_in):
       response = test_api_logged_in.get('/some-endpoint/')
       assert response.status_code == 200
   ```

2. **Autouse**: Mark fixtures with `autouse=True` to apply them automatically to all tests in scope

   ```python
   @pytest.fixture(autouse=True)
   def insert_testing_data():
       insert_test_data('tasks')
       yield
       delete_test_data('tasks')
   ```

## Fixture Dependencies

Fixtures can depend on other fixtures to build complex test setups. For example:

```python
@pytest.fixture
def test_feature(test_api_logged_in, insert_testing_data):
    # This fixture depends on both an authenticated API client
    # and test data being available
    ...
```

## Dynamic Fixture Analysis

The diagram at the top of this page is generated dynamically from the actual fixture code in the project. This ensures it always reflects the current state of the testing infrastructure. Additional visualizations of the fixture hierarchy:

- [Fixture Scope Hierarchy](../images/generated/fixture_scopes.svg) - Shows the pytest fixture scope levels
- [Fixture Dependencies](../images/generated/fixture_dependencies.svg) - Dependencies between fixtures
- [Comprehensive Fixture View](../images/generated/fixtures_comprehensive.svg) - Complete view of all fixtures

## Best Practices

1. Use the appropriate fixture scope to optimize test performance
2. Keep fixtures focused on a single responsibility
3. Use `autouse=True` sparingly to avoid confusion
4. Document fixture dependencies clearly
5. Clean up test data in fixture teardown phases
