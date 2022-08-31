import time
from typing import Any, Generator

import docker
import pytest
from docker.errors import DockerException
from euphoria.backend.common.config import env_config
from euphoria.backend.common.db.sqlalchemy.base import Base
from euphoria.backend.common.db.sqlalchemy.session import sqlalchemy_session
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema
from euphoria.backend.common.config import env_config

engine = create_engine('postgresql://postgres:postgres@localhost:5434', echo=True, future=True)
SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_testing_session() -> Session:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope='module')
def postgres_testdb_in_docker():
    """Create a postgres test database in docker for unit tests

    parameter test_data should be defined in the testing_file as:
    `@pytest.fixture(autouse=True)`
    `def test_data() -> list[dict]:

    Port number needs to be something different from the default in case
    postgres is running locally also

    `auto_remove` will destroy the container once it is stopped.
    Use `testdb.stop()` to stop the container after testing
    """
    try:
        docker_client = docker.DockerClient()
        testdb = docker_client.containers.run(
            'postgres:14',
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
        time.sleep(2)  # Must sleep to allow creation of detached Docker container

        # SQLAlchemy will not create the schemas automatically
        def create_schemas(schemas, db_session):
            session = next(db_session())
            for schema_name in schemas:
                session.execute(CreateSchema(schema_name))
            session.commit()
            session.close()

        create_schemas(env_config.SCHEMAS, get_testing_session)

        yield testdb
    except DockerException as e:
        print(e)
        pytest.exit('Failed to Initialize Postgres in Docker')
    finally:
        testdb.stop()


@pytest.fixture(scope='function')
def insert_test_data(test_data, data_model):
    session = next(get_testing_session())
    Base.metadata.create_all(engine)
    for datum in test_data:
        session.add(data_model(**datum))
    session.commit()
    yield
    Base.metadata.drop_all(engine)
    session.close()


@pytest.fixture(scope='function')
def test_app(router: APIRouter) -> Generator[TestClient, Any, None]:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[sqlalchemy_session] = get_testing_session
    with TestClient(app) as client:
        yield client
