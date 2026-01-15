"""Reset test database to clean state.

This script ONLY works with the testing environment and ONLY on localhost:5434.
It drops all tables and recreates them fresh for a guaranteed clean test state.

Usage:
    python -m ichrisbirch.database.reset_test_database

This is intentionally separate from ichrisbirch.database.initialization to prevent
any possibility of accidentally running destructive operations on production.
"""

import os
import sys

# Hard-coded safety checks - this script ONLY works for testing
REQUIRED_ENV = 'testing'
REQUIRED_HOST = 'localhost'
REQUIRED_PORT = '5434'


def main():
    # Force testing environment
    os.environ['ENVIRONMENT'] = REQUIRED_ENV
    os.environ['POSTGRES_HOST'] = REQUIRED_HOST
    os.environ['POSTGRES_PORT'] = REQUIRED_PORT

    # Import after setting environment
    import structlog

    from ichrisbirch.config import get_settings
    from ichrisbirch.database.base import Base
    from ichrisbirch.database.initialization import create_schemas
    from ichrisbirch.database.initialization import create_tables
    from ichrisbirch.database.initialization import insert_default_users
    from ichrisbirch.database.session import create_session
    from ichrisbirch.database.session import get_db_engine

    logger = structlog.get_logger()

    settings = get_settings()

    # Triple-check we're in testing environment on correct host/port
    if settings.ENVIRONMENT != REQUIRED_ENV:
        logger.error('SAFETY CHECK FAILED', expected=REQUIRED_ENV, actual=settings.ENVIRONMENT)
        sys.exit(1)
    if settings.postgres.host != REQUIRED_HOST:
        logger.error('SAFETY CHECK FAILED', expected_host=REQUIRED_HOST, actual=settings.postgres.host)
        sys.exit(1)
    if str(settings.postgres.port) != REQUIRED_PORT:
        logger.error('SAFETY CHECK FAILED', expected_port=REQUIRED_PORT, actual=settings.postgres.port)
        sys.exit(1)

    logger.warning('test_db_reset_starting', environment=settings.ENVIRONMENT, host=settings.postgres.host, port=settings.postgres.port)

    # Drop all tables
    logger.warning('dropping_all_tables')
    engine = get_db_engine(settings)
    Base.metadata.drop_all(engine)
    logger.warning('tables_dropped')

    # Recreate fresh
    with create_session(settings) as session:
        create_schemas(session, settings)
        create_tables(settings)
        insert_default_users(session, settings)

    logger.warning('test_db_reset_completed')


if __name__ == '__main__':
    main()
