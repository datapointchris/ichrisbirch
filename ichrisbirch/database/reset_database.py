"""Reset development or testing database to clean state.

Drops all tables and recreates them fresh. Intended for local dev and test
environments only — production is rejected outright, and each env is pinned
to its expected host:port so a misconfigured `.env` can't target the wrong DB.

Usage:
    ENVIRONMENT=development python -m ichrisbirch.database.reset_database
    ENVIRONMENT=testing     python -m ichrisbirch.database.reset_database

This is intentionally separate from ichrisbirch.database.initialization so
destructive operations live in one clearly-named module.
"""

import os
import sys

ALLOWED_ENVIRONMENTS = {
    'development': {'host': 'localhost', 'port': '5432'},
    'testing': {'host': 'localhost', 'port': '5434'},
}


def main():
    env = os.environ.get('ENVIRONMENT', '')

    if env not in ALLOWED_ENVIRONMENTS:
        print(
            f'SAFETY CHECK FAILED: ENVIRONMENT must be one of {sorted(ALLOWED_ENVIRONMENTS)}, got {env!r}',
            file=sys.stderr,
        )
        sys.exit(1)

    expected = ALLOWED_ENVIRONMENTS[env]
    os.environ['POSTGRES_HOST'] = expected['host']
    os.environ['POSTGRES_PORT'] = expected['port']

    import structlog

    from ichrisbirch.config import get_settings
    from ichrisbirch.database.initialization import create_schemas
    from ichrisbirch.database.initialization import create_tables
    from ichrisbirch.database.initialization import drop_all_tables
    from ichrisbirch.database.initialization import insert_default_users
    from ichrisbirch.database.session import create_session

    logger = structlog.get_logger()
    settings = get_settings()

    if env != settings.ENVIRONMENT:
        logger.error('SAFETY CHECK FAILED', expected=env, actual=settings.ENVIRONMENT)
        sys.exit(1)
    if settings.postgres.host != expected['host']:
        logger.error('SAFETY CHECK FAILED', expected_host=expected['host'], actual=settings.postgres.host)
        sys.exit(1)
    if str(settings.postgres.port) != expected['port']:
        logger.error('SAFETY CHECK FAILED', expected_port=expected['port'], actual=settings.postgres.port)
        sys.exit(1)

    logger.info(
        'db_reset_starting',
        environment=settings.ENVIRONMENT,
        host=settings.postgres.host,
        port=settings.postgres.port,
    )

    drop_all_tables(settings)

    with create_session(settings) as session:
        create_schemas(session, settings)
        create_tables(settings)
        insert_default_users(session, settings)

    logger.info('db_reset_completed')


if __name__ == '__main__':
    main()
