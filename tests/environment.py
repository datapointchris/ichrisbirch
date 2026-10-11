"""The Postgres and Redis a pytest session runs against.

Every session starts its own pair on ports Docker picks, so two checkouts run
pytest at once and neither can truncate the other's tables. testcontainers'
reaper removes both when the session ends, however it ends.
"""

import logging
from pathlib import Path

import pytest
import yaml
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer
from testcontainers.core.config import testcontainers_config
from testcontainers.core.container import DockerContainer

from ichrisbirch.config import Settings
from ichrisbirch.database.initialization import full_initialization

logger = logging.getLogger(__name__)

# Readiness is checked every 100ms instead of every second, under the same two-minute ceiling.
testcontainers_config.sleep_time = 0.1
testcontainers_config.max_tries = 1200

REPO_ROOT = Path(__file__).resolve().parents[1]
POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = 'postgres'
POSTGRES_DB = 'ichrisbirch'
POSTGRES_DATA = '/var/lib/postgresql/data'


def production_image(service: str) -> str:
    """The image production runs a service on, so the tests meet the same major version."""
    compose = yaml.safe_load((REPO_ROOT / 'docker-compose.yml').read_text())
    return compose['services'][service]['image']


class PrivateServices:
    """Starts this session's Postgres and Redis and points `settings` at them."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Durability is off and the data lives in memory: nothing outlives the session.
        self.postgres = (
            PostgresContainer(
                production_image('postgres'), username=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB, driver=None
            )
            .with_tmpfs_mount(POSTGRES_DATA)
            .with_command(['postgres', '-c', 'fsync=off', '-c', 'synchronous_commit=off', '-c', 'full_page_writes=off'])
        )
        self.redis = RedisContainer(production_image('redis')).with_command(['redis-server', '--save', '', '--appendonly', 'no'])
        self.started: list[DockerContainer] = []

    def __enter__(self):
        try:
            self.start()
        except Exception as e:
            self.stop()
            pytest.exit(f'Could not start the Postgres and Redis this session runs against: {e}', returncode=1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def start(self) -> None:
        for container in (self.redis, self.postgres):
            container.start()
            self.started.append(container)
        postgres_host = self.postgres.get_container_host_ip()
        postgres_port = self.postgres.get_exposed_port(5432)
        for database in (self.settings.postgres, self.settings.sqlalchemy):
            database.host = postgres_host
            database.port = postgres_port
            database.username = POSTGRES_USER
            database.password = POSTGRES_PASSWORD
            database.database = POSTGRES_DB
        self.settings.redis.host = self.redis.get_container_host_ip()
        self.settings.redis.port = self.redis.get_exposed_port(6379)
        self.settings.redis.password = ''
        logger.info(
            f'session services: postgres {postgres_host}:{postgres_port}, redis {self.settings.redis.host}:{self.settings.redis.port}'
        )
        full_initialization(self.settings)

    def stop(self) -> None:
        while self.started:
            self.started.pop().stop()
