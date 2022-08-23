from typing import Any
from typing import Generator
import time
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
import sqlalchemy
import random
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.schema import CreateSchema
import docker

import sys
import os

from backend.common.db.sqlalchemy.session import sqlalchemy_session
from backend.common.db.sqlalchemy.base_class import Base
from backend.common.models.tasks import Task
from backend.api.endpoints import tasks



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


def create_app_with_routes():
    app = FastAPI()
    app.include_router(tasks.router)
    return app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `sqlalchemy_testing_session` fixture to override
    the `sqlalchemy_session` dependency that is injected into routes.
    """
    # 1. Create docker container with postgres
    testdb = create_postgres_in_docker()

    # # # MUST SLEEP # # #
    # or engine will create before container is started and give `ConnectionRefusedError`
    # This is because the container has to detach or it holds up the script
    time.sleep(2)

    # 2. Create engine and session
    engine = create_engine("postgresql://postgres:postgres@localhost:5434", echo=False, future=True)
    SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    def sqlalchemy_testing_session() -> Session:
        """Generate testing session for dependency override"""
        session = SessionTesting()
        try:
            yield session
        finally:
            session.close()

    # 3. Create the schemas and tables
    # Note: SQLAlchemy will not create the schemas automatically
    schemas = ['apartments', 'habits', 'moving', 'portfolio', 'priorities', 'tasks', 'tracks']
    with SessionTesting() as session:
        for schema_name in schemas:
            session.execute(CreateSchema(schema_name))
        session.commit()

    Base.metadata.create_all(engine)

    # Create test data
    # TODO: Find how to do this per testing file
    def test_tasks(num: int = 1000) -> list[dict]:
        return [
            {
                "name": f"task-{num:03}",
                "category": f"category-{num:03}",
                "priority": random.randint(1, 100),
            }
            for num in range(num)
        ]

    # Insert the test data
    with SessionTesting() as session:
        for task in test_tasks():
            session.add(Task(**task))
        session.commit()

    # 4. Create the app
    app = create_app_with_routes()

    # 5. Replace regular session with testing session
    app.dependency_overrides[sqlalchemy_session] = sqlalchemy_testing_session

    # 6. Use TestClient to mimic requests
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # 6. Always delete the tables and stop the container when finished
        Base.metadata.drop_all(engine)
        testdb.stop()
