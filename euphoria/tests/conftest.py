from typing import Any
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.expression import text
import docker

import sys
import os

from backend.common.db.sqlalchemy.session import sqlalchemy_session
from backend.common.db.sqlalchemy.base_class import Base
from backend.api.endpoints import tasks


def run_postgres_in_docker():
    """Create a postgres test database in docker for unit tests

    Port number needs to be something different from the default in case
    postgres is running locally also

    `auto_remove` will destroy the container once it is stopped.
    Use `testdb.stop()` to stop the container after testing


    """
    client = docker.DockerClient()
    testdb = client.containers.run(
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


def start_application():
    app = FastAPI()
    app.include_router(tasks.router)
    return app


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """

    _app = start_application()
    yield _app
    Base.metadata.drop_all(engine)


# @pytest.fixture(scope="function")
# def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = SessionTesting(bind=connection)
#     yield session  # use the session in tests.
#     session.close()
#     transaction.rollback()
#     connection.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `sqlalchemy_session` dependency that is injected into routes.
    """

    SQLALCHEMY_DATABASE_URL = "postgresql://localhost:5434"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, echo=False, future=True
    )
    # Use connect_args parameter only with sqlite
    SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    schemas = ['apartments', 'habits', 'moving', 'portfolio', 'priorities', 'tasks', 'tracks']
    with SessionTesting() as session:
        session.execute(text("CREATE DATABASE euphoria"))
        for schema_name in schemas:  # SQLAlchemy will not create the schemas
            session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    Base.metadata.create_all(engine)  # Create the tables.

    app = FastAPI()
    app.include_router(tasks.router)

    def _get_test_db() -> Session:
        session = SessionTesting()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[sqlalchemy_session] = _get_test_db
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(engine)
