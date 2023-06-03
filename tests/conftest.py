import logging
import time
from typing import Any, Generator

import docker
import pytest
from docker.errors import DockerException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.db.sqlalchemy.base import Base
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

settings = get_settings()
logger = logging.getLogger(__name__)
engine = create_engine('postgresql://postgres:postgres@localhost:5434', echo=False, future=True)
SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def create_postgres_docker_container():
    """Create a postgres instance in a docker container

    Port number needs to be something different from the default in case
    postgres is running locally also

    `auto_remove` will destroy the container once it is stopped.

    Returns:
        Model (Container) : docker container
    """
    try:
        docker_client = docker.DockerClient()
        container = docker_client.containers.run(
            image='postgres:14',
            detach=True,
            environment={
                'ENVIRONMENT': 'development',
                'POSTGRES_USER': 'postgres',
                'POSTGRES_PASSWORD': 'postgres',
            },
            name='testdb',
            ports={5432: 5434},
            mem_limit='2g',
            auto_remove=True,
        )
    except DockerException as e:
        pytest.exit(f'Failed to RUN Docker client: {e}')

    time.sleep(2)  # Must sleep to allow creation of detached Docker container
    return container


def get_testing_session() -> Generator:
    """Get SQLAlchemy Session for testing"""
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def create_schemas(schemas: list[str]):
    """Create schemas in the db

    SQLAlchemy will not create the schemas automatically
    """
    session = next(get_testing_session())
    try:
        for schema_name in schemas:
            session.execute(CreateSchema(schema_name))
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope='session')
def postgres_testdb_in_docker():
    """Create a postgres test database in docker for unit tests

    parameter test_data should be defined in the testing_file as:
    `@pytest.fixture(autouse=True)`
    `def test_data() -> list[dict]:

    Use `testdb.stop()` to stop the container after testing
    """
    container = create_postgres_docker_container()
    create_schemas(settings.db_schemas)
    try:
        yield container
    finally:
        container.stop()  # type: ignore


@pytest.fixture(scope='function')
def insert_test_data(postgres_testdb_in_docker, test_data):
    """Insert test data into db"""
    session = next(get_testing_session())
    Base.metadata.create_all(engine)
    for record in test_data:
        session.add(record)
    session.commit()
    yield
    Base.metadata.drop_all(engine)
    session.close()


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    """Create a FastAPI app for testing"""
    api = create_api(settings=settings)
    api.dependency_overrides[sqlalchemy_session] = get_testing_session
    with TestClient(api) as client:
        yield client


@pytest.fixture(scope='module')
def test_app():
    """Create a Flask app for testing"""
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    with app.test_client() as client:
        with app.app_context():
            yield client
