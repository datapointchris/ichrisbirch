from ichrisbirch.config import settings


def test_env_file():
    """Test if env file is set correctly"""
    assert settings.env_file.split('/')[-1] == '.dev.env'


def test_postgres_db_uri():
    """Test if postgres db uri is set correctly"""
    assert settings.postgres.db_uri == 'postgresql://postgres:postgres@localhost:5432/ichrisbirch'


def test_sqlalchemy_db_uri():
    """Test if sqlalchemy db uri is set correctly"""
    assert settings.sqlalchemy.db_uri == 'postgresql://postgres:postgres@localhost:5432/ichrisbirch'


def test_os_prefix():
    """Test if os prefix is set correctly"""
    assert settings.os_prefix == '/usr/local'


def test_log_path():
    """Test if log path is set correctly"""
    assert settings.logging.log_dir == '/usr/local/var/log/ichrisbirch'
