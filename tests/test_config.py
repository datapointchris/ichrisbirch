import os

from ichrisbirch.config import get_settings
from tests.helpers import find_project_root

string_path = find_project_root() / '.dev.env'
test_env_file = find_project_root() / 'tests' / 'testing_data' / '.test_env_file.env'


def test_load_environment_by_ENVIRONMENT_variable():
    """Test if settings can be loaded by ENVIRONMENT variable."""
    os.environ['ENVIRONMENT'] = 'development'
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.ENVIRONMENT == 'development'
    assert settings.ENV_FILE.name == '.dev.env'


def test_load_environment_by_string():
    """Test if settings can be loaded by string choice."""
    get_settings.cache_clear()
    settings = get_settings('testing')
    assert settings.ENVIRONMENT == 'testing'
    assert settings.ENV_FILE.name == '.test.env'


def test_load_environment_by_string_path():
    """Test if settings can be loaded by string path."""
    get_settings.cache_clear()
    settings = get_settings(str(string_path))
    assert settings.ENVIRONMENT == 'development'
    assert settings.ENV_FILE.name == '.dev.env'


def test_load_environment_by_path():
    """Test if settings can be loaded by pathlib.Path."""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.ENVIRONMENT == 'testing'
    assert settings.ENV_FILE.name == '.test_env_file.env'


def test_postgres_user():
    """Test if postgres user is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.postgres.username == 'postgres-test'


def test_postgres_db_uri():
    """Test if postgres db uri is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.postgres.db_uri == 'postgresql://postgres-test:postgres@localhost:5434/ichrisbirch'


def test_sqlalchemy_db_uri():
    """Test if sqlalchemy db uri is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.sqlalchemy.db_uri == 'postgresql://postgres-test:postgres@localhost:5434/ichrisbirch'
