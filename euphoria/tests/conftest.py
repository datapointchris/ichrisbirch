import random
import time
from typing import Any, Generator

import docker
import pytest
from backend.api.endpoints import tasks
from backend.common.db.sqlalchemy.base_class import Base
from backend.common.db.sqlalchemy.session import sqlalchemy_session
from backend.common.models.tasks import Task
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema

SCHEMAS = ['apartments', 'habits', 'moving', 'portfolio', 'priorities', 'tasks', 'tracks']


def insert_test_data_in_db(test_data: callable, db_session: Session, data_model):
    session = next(db_session())
    for datum in test_data:
        session.add(data_model(**datum))
    session.commit()


def create_postgres_in_docker():
    """Create a postgres test database in docker for unit tests

    Port number needs to be something different from the default in case
    postgres is running locally also

    `auto_remove` will destroy the container once it is stopped.
    Use `testdb.stop()` to stop the container after testing
    """
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
    return testdb


engine = create_engine("postgresql://postgres:postgres@localhost:5434", echo=False, future=True)
SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db_session() -> Session:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def create_db_schemas(schemas, engine, db_session):
    session = next(db_session())
    for schema_name in schemas:
        session.execute(CreateSchema(schema_name))
    session.commit()


def create_app_with_routes():
    app = FastAPI()
    app.include_router(tasks.router)
    return app


@pytest.fixture(scope="session")
def setup_test_db():
    testdb = create_postgres_in_docker()
    time.sleep(2)  # Must sleep to allow creation of detached Docker container
    create_db_schemas(SCHEMAS, engine, get_db_session)
    yield
    testdb.stop()


@pytest.fixture(scope="function")
def client(setup_test_db, test_data) -> Generator[TestClient, Any, None]:
    # the `setup_test_db` must be included or else it won't be run on the first call
    """
    Create a new FastAPI TestClient that uses the `sqlalchemy_testing_session` fixture to override
    the `sqlalchemy_session` dependency that is injected into routes.
    """
    # 1. Create docker container with postgres

    # # # MUST SLEEP # # #
    # or engine will create before container is started and give `ConnectionRefusedError`
    # This is because the container has to detach or it holds up the script
    # time.sleep(2)

    # 2. Create engine and session

    # 3. Create the schemas and tables
    # Note: SQLAlchemy will not create the schemas automatically
    Base.metadata.create_all(engine)

    # Create test data

    # Insert the test data
    insert_test_data_in_db(test_data, db_session=get_db_session, data_model=Task)

    # 4. Create the app
    app = create_app_with_routes()

    app.dependency_overrides[sqlalchemy_session] = get_db_session

    # 6. Use TestClient to mimic requests
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # 6. Always delete the tables and stop the container when finished
        # testing_session = next(get_db_session())
        Base.metadata.drop_all(engine)
        # for table in reversed(Base.metadata.sorted_tables):
        #     testing_session.execute(table.delete())
        # testing_session.commit()
        # testdb.stop()
