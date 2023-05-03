from ichrisbirch.config import settings


def test_postgres_db_uri():
    """Test if postgres db uri is set correctly"""
    assert settings.postgres.db_uri == 'postgresql://postgres:postgres@localhost:5432/ichrisbirch'
