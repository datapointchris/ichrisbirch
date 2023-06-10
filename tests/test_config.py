import os

from ichrisbirch.config import get_settings
from tests.helpers import find_project_root

string_path = find_project_root() / '.dev.env'
test_env_file = find_project_root() / 'tests' / 'test_env_file'


def test_load_environment_by_ENVIRONMENT_variable():
    """Test if settings can be loaded by ENVIRONMENT variable"""
    os.environ['ENVIRONMENT'] = 'development'
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.environment == 'development'
    assert settings.env_file.name == '.dev.env'


def test_load_environment_by_string():
    """Test if settings can be loaded by string choice"""
    get_settings.cache_clear()
    settings = get_settings('testing')
    assert settings.environment == 'testing'
    assert settings.env_file.name == '.test.env'


def test_load_environment_by_string_path():
    """Test if settings can be loaded by string path"""
    get_settings.cache_clear()
    settings = get_settings(str(string_path))
    assert settings.environment == 'development'
    assert settings.env_file.name == '.dev.env'


def test_load_environment_by_path():
    """Test if settings can be loaded by pathlib.Path"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.environment == 'testing'
    assert settings.env_file.name == 'test_env_file'


def test_postgres_user():
    """Test if postgres user is set correctly"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.postgres.user == 'postgres-test'


def test_postgres_db_uri():
    """Test if postgres db uri is set correctly"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.postgres.db_uri == 'postgresql://postgres-test:postgres@localhost:5432/ichrisbirch'


def test_sqlalchemy_db_uri():
    """Test if sqlalchemy db uri is set correctly"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.sqlalchemy.db_uri == 'postgresql://postgres-test:postgres@localhost:5432/ichrisbirch'


def test_os_prefix():
    """Test if os prefix is set correctly"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.os_prefix == '/usr/local'


def test_log_path():
    """Test if log path is set correctly"""
    get_settings.cache_clear()
    settings = get_settings(env_file=test_env_file)
    assert settings.logging.log_dir == '/usr/local/var/log/ichrisbirch'
