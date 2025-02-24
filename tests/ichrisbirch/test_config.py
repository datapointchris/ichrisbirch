import os

from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

string_path = find_project_root() / '.dev.env'
TEST_ENV_FILE = find_project_root() / 'tests' / 'test_data' / '.test_env_file.env'


def test_load_environment_by_ENVIRONMENT_variable():
    """Test if settings can be loaded by ENVIRONMENT variable."""
    os.environ['ENVIRONMENT'] = 'development'
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.ENVIRONMENT == 'development', 'ENVIRONMENT should be development'
    assert settings.env_file.name == '.dev.env'


def test_load_environment_by_string():
    """Test if settings can be loaded by string choice."""
    get_settings.cache_clear()
    settings = get_settings('testing')
    assert settings.ENVIRONMENT == 'testing', 'ENVIRONMENT should be testing'
    assert settings.env_file.name == '.test.env'


def test_load_environment_by_string_path():
    """Test if settings can be loaded by string path."""
    get_settings.cache_clear()
    settings = get_settings(str(string_path))
    assert settings.ENVIRONMENT == 'development', 'ENVIRONMENT should be development'
    assert settings.env_file.name == '.dev.env'


def test_load_environment_by_path():
    """Test if settings can be loaded by pathlib.Path."""
    get_settings.cache_clear()
    settings = get_settings(env_file=TEST_ENV_FILE)
    assert settings.ENVIRONMENT == 'testing', 'ENVIRONMENT should be testing'
    assert settings.env_file.name == '.test_env_file.env'


def test_postgres_user():
    """Test if postgres user is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=TEST_ENV_FILE)
    assert settings.postgres.username == 'postgres-test', 'postgres username should be postgres-test'


def test_postgres_db_uri():
    """Test if postgres db uri is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=TEST_ENV_FILE)
    testing_uri = 'postgresql://postgres-test:postgres@127.0.0.1:5434/ichrisbirch'
    assert settings.postgres.db_uri == testing_uri, f'postgres db uri should be {testing_uri}'


def test_sqlalchemy_db_uri():
    """Test if sqlalchemy db uri is set correctly."""
    get_settings.cache_clear()
    settings = get_settings(env_file=TEST_ENV_FILE)
    testing_uri = 'postgresql://postgres-test:postgres@127.0.0.1:5434/ichrisbirch'
    assert settings.sqlalchemy.db_uri == testing_uri, f'sqlalchemy db uri should be {testing_uri}'
