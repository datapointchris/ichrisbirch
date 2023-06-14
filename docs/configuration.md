# Configuration

## `ichrisbirch/ichrisbirch/config.py`

In the Config class, we're setting the env_file based on the ENVIRONMENT variable. If ENVIRONMENT is not recognized, env_file will be None. When env_file is set, pydantic will automatically try to load the variables from the specified file.

Also note that since pydantic automatically converts environment variables to their corresponding data types, we don't need to use Optional or Union in our field definitions anymore.

### Flake 8

`.flake8` cannot be loaded from `pyproject.toml`

