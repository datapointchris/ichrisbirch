import logging
import subprocess
import threading
import time
from typing import Any, Generator

import docker
import pytest
from docker.errors import DockerException
from docker.models.containers import Container
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

settings = get_settings()
logger = logging.getLogger(__name__)

engine = create_engine('postgresql://postgres:postgres@localhost:5434', echo=False, future=True)
# engine = create_engine(settings.sqlalchemy.db_uri, echo=False, future=True)
SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

docker_client = docker.APIClient(base_url='unix://var/run/docker.sock')
postgres_container_config = dict(
    image='postgres:14',
    name='postgres_testing',
    environment={'ENVIRONMENT': 'testing', 'POSTGRES_USER': 'postgres', 'POSTGRES_PASSWORD': 'postgres'},
    ports=[5432],
    host_config=docker_client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
    detach=True,
    labels=['testing'],
)


def create_docker_container(config: dict[str, Any]) -> Container:
    try:
        image = config.pop('image')
        container = docker_client.create_container(image, **config)
    except DockerException as e:
        message = f'Failed to RUN Docker client: {e}'
        logger.error(message)
        pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    for log in docker_client.logs(container=container.get('Id'), stream=True):
        print(log.strip())
        logging.info(log.strip())
    return container


def get_testing_session() -> Generator[Session, None, None]:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def create_db_schemas(schemas: list[str]) -> None:
    # SQLAlchemy will not create the schemas automatically
    session = next(get_testing_session())
    try:
        for schema_name in schemas:
            session.execute(CreateSchema(schema_name))
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    # Create Postgres Docker container
    postgres_docker_container = create_docker_container(postgres_container_config)
    postgres_thread = threading.Thread(
        target=docker_client.start, kwargs={'container': postgres_docker_container.get('Id')}
    )
    postgres_thread.start()
    time.sleep(3)  # Allow Postgres to start

    # Create DB schemas in Postgres container
    create_db_schemas(settings.db_schemas)

    # Start Uvicorn FastAPI subprocess (for testing APP, that needs an API response)
    # This is easier than mocking everything
    uvicorn_command = 'uvicorn ichrisbirch.api.main:create_api --factory --host localhost --port 5555 --log-level debug'
    uvicorn_process = subprocess.Popen(uvicorn_command.split())
    uvicorn_thread = threading.Thread(target=uvicorn_process.wait)
    # uvicorn_thread = threading.Thread(target=subprocess.Popen, args=(uvicorn_command.split(),))
    uvicorn_thread.start()
    time.sleep(1)  # Allow Uvicorn FastAPI to start

    try:
        yield
    finally:
        # Stop container and join thread to main thread
        docker_client.stop(container=postgres_docker_container.get('Id'))
        postgres_thread.join()
        # Kill uvicorn process and join thread to main thread
        uvicorn_process.kill()
        uvicorn_thread.join()


@pytest.fixture(scope='function')
def insert_test_data(test_data):
    """Insert test data into db"""
    session = next(get_testing_session())
    Base.metadata.create_all(engine)
    for record in test_data:
        session.add(record)
    session.commit()
    session.close()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    """Create a FastAPI app for testing"""
    api = create_api()
    api.dependency_overrides[sqlalchemy_session] = get_testing_session
    with TestClient(api) as client:
        yield client


@pytest.fixture(scope='module')
def test_app():
    """Create a Flask app for testing"""
    app = create_app()
    app.testing = True
    app.config.update({'TESTING': True})
    with app.test_client() as client:
        with app.app_context():
            yield client
