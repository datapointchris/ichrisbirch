# Testing Configuration

This document explains the updated approach to handling configuration in the testing environment.

## Key Changes

1. Eliminated the need for the `ENVIRONMENT` variable
2. Moved to a single `.env` file approach
3. Hardcoded test settings for more reliable testing
4. Removed the environment-specific `.dev.env`, `.test.env`, and `.prod.env` files

## How It Works

### Test Settings

Test settings are now defined in a centralized location:

```python
# In tests/utils/test_settings.py
TEST_ENV_VARS = {
    "ENVIRONMENT": "testing",
    "PROTOCOL": "http",
    # ... more hardcoded test settings
}
```

These settings are used consistently throughout the test environment. This eliminates the need to set the `ENVIRONMENT` variable and makes tests more reliable.

### Accessing Test Settings

To get test settings, use:

```python
from tests.utils.settings import get_test_settings

settings = get_test_settings()
```

This function returns a Settings object initialized with the hardcoded test values, not environment variables or `.env` files.

### Production Settings

In production, settings are now loaded from a single `.env` file in the project root, instead of using environment-specific files. This simplifies deployment and configuration.

### Running Tests

To run tests, you no longer need to set the `ENVIRONMENT` variable:

```bash
# Old approach (no longer needed)
ENVIRONMENT=testing poetry run pytest

# New approach
poetry run pytest
```

Tests will automatically use the hardcoded test settings.

## Benefits

1. **Reliability**: Tests are no longer affected by the environment they run in
2. **Simplicity**: No need to manage multiple `.env` files
3. **Consistency**: All tests use the same configuration
4. **Isolation**: Test environment is isolated from production environment

## Implementation Details

The key implementation changes are:

1. `get_settings()` function in `config.py` now accepts a `test_mode` parameter
2. When `test_mode=True`, it uses hardcoded test settings instead of loading from `.env` files
3. TestEnvironment class uses these settings for the test infrastructure
4. All test fixtures and utilities use the same settings consistently
