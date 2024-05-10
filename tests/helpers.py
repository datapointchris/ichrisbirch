import logging
import pathlib
import subprocess
import time
from copy import deepcopy
from typing import Any
from typing import Generator

import docker
import httpx
import pytest
from docker.errors import DockerException
from docker.models.containers import Container
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

import tests.test_data
from ichrisbirch.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings('testing')
logger.info(f"load settings from environment: {settings.ENVIRONMENT}")

ENGINE = create_engine(settings.sqlalchemy.db_uri, echo=False, future=True)
SessionTesting = sessionmaker(bind=ENGINE, autocommit=False, autoflush=True, future=True, expire_on_commit=False)


def show_status_and_response(response: httpx.Response) -> dict[str, str]:
    """Convert status code to description and return response if any."""
    d = {}
    for attr in dir(status):
        code = attr.split('_')[1]
        d[int(code)] = attr
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError):
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}


def find_project_root(
    directory: pathlib.Path = pathlib.Path.cwd(),
    target_file: str = 'pyproject.toml',
) -> pathlib.Path:
    """Find the project root directory."""
    for file in directory.iterdir():
        if file.name == target_file:
            return directory.absolute()
    parent_directory = directory.parent
    if parent_directory == directory:
        raise FileNotFoundError(f'Could not find project root directory searching for {target_file}')
    return find_project_root(parent_directory)


def get_docker_client() -> docker.APIClient:
    try:
        return docker.APIClient(base_url='unix://var/run/docker.sock')
    except DockerException:
        # Docker is not running
        print('docker is not running, starting...')
        subprocess.run(['open', '-ga', 'docker'])
        subprocess.run(['sleep', '20'])
        print('docker started')
        # Try again, let failure surface in the next command if this was not the issue
        return docker.APIClient(base_url='unix://var/run/docker.sock')


def create_docker_container(client: docker.APIClient, config: dict[str, Any]) -> Container:
    image = config.pop("image")
    try:
        client.pull(image)
        container = client.create_container(image, **config)
    except DockerException as e:
        message = f"Failed to CREATE Docker client: {e}"
        logger.error(message)
        try:
            client.remove_container(container=config.get("name"), force=True)
            container = client.create_container(image, **config)
        except DockerException as e:
            message = f"Failed to REMOVE and RECREATE Docker container: {e}"
            logger.error(message)
            pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    # TODO: I don't think this works, need to see when logging is fixed
    for log in client.logs(container=container.get("Id"), stream=True):
        logger.info(log.strip())
    return container


def get_testing_session() -> Generator[Session, None, None]:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def insert_test_data() -> None:
    """Insert testing data for each endpoint.

    The data is manually added, must update when a new endpoint is added. deepcopy(data) is necessary or the tests will
    mutate the BASE_DATA and cause test failures
    """
    base_datasets = [
        tests.test_data.autotasks.BASE_DATA,
        tests.test_data.boxes.BASE_DATA,
        tests.test_data.boxitems.BASE_DATA,
        tests.test_data.countdowns.BASE_DATA,
        tests.test_data.events.BASE_DATA,
        tests.test_data.tasks.BASE_DATA,
    ]
    with SessionTesting() as session:
        for data in base_datasets:
            session.add_all(deepcopy(data))
        session.commit()
