import time
from typing import Any, Generator

import docker
import pytest
from docker.errors import DockerException
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import settings
from ichrisbirch.db.sqlalchemy.base import Base
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

engine = create_engine('postgresql://postgres:postgres@localhost:5434', echo=True, future=True)
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


@pytest.fixture(scope='module')
def postgres_testdb_in_docker():
    """Create a postgres test database in docker for unit tests

    parameter test_data should be defined in the testing_file as:
    `@pytest.fixture(autouse=True)`
    `def test_data() -> list[dict]:

    Use `testdb.stop()` to stop the container after testing
    """
    container = create_postgres_docker_container()
    create_schemas(settings.DB_SCHEMAS)
    try:
        yield container
    finally:
        container.stop()  # type: ignore


@pytest.fixture(scope='function')
def insert_test_data(base_test_data: list[dict], data_model):
    """Insert test data into db using the supplied SQLAlchemy model (data_model)"""
    session = next(get_testing_session())
    Base.metadata.create_all(engine)
    for data in base_test_data:
        session.add(data_model(**data))
    session.commit()
    yield
    Base.metadata.drop_all(engine)
    session.close()


@pytest.fixture(scope='function')
def test_app(router: APIRouter) -> Generator[TestClient, Any, None]:
    """Create a FastAPI app for testing"""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[sqlalchemy_session] = get_testing_session
    with TestClient(app) as client:
        yield client
