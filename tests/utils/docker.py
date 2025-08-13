"""Docker utilities for testing.

This module provides functions for Docker container management.
"""

import contextlib
import logging
import subprocess
import time
from typing import Any

import docker
import pytest
from docker.errors import DockerException

logger = logging.getLogger(__name__)


def get_docker_client(logger: logging.Logger) -> docker.APIClient:
    """Get Docker client, starting Docker if necessary.

    Args:
        logger: Logger instance for logging Docker status

    Returns:
        Docker API client

    Raises:
        pytest.exit: If Docker cannot be started
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            client = docker.APIClient(base_url='unix://var/run/docker.sock')
            # Test the connection
            client.ping()
            return client
        except DockerException as e:
            logger.warning(f'docker connection failed (attempt {attempt + 1}/{max_retries}): {e}')
            if attempt == 0:
                logger.warning('Starting Docker desktop application...')
                try:
                    subprocess.run(['open', '-ga', 'Docker'], check=True)
                    # Wait longer on first attempt to allow Docker to fully start
                    logger.info(f'Waiting {retry_delay * 4} seconds for Docker to start')
                    time.sleep(retry_delay * 4)
                except subprocess.SubprocessError as se:
                    logger.error(f'Failed to start Docker: {se}')
            else:
                logger.info(f'Waiting {retry_delay} seconds before retry')
                time.sleep(retry_delay)

    message = 'failed to connect to Docker after several attempts. Please ensure Docker is running.'
    logger.error(message)
    pytest.exit(message)


def create_docker_container(client: docker.APIClient, config: dict[str, Any]):
    """Create a Docker container with the specified configuration.

    Args:
        client: Docker API client
        config: Container configuration

    Returns:
        Created container

    Raises:
        pytest.exit: If container creation fails
    """
    image = config.pop('image')
    container_name = config.get('name', '')

    # Check if container already exists, remove it if it does
    try:
        existing_containers = client.containers(all=True, filters={'name': container_name})
        if existing_containers:
            logger.warning(f'container {container_name} already exists, removing it')
            client.remove_container(container=container_name, force=True)
    except DockerException as e:
        logger.warning(f'error checking for existing container: {e}')

    # Pull the image with retries
    for attempt in range(3):
        try:
            logger.info(f'pulling Docker image: {image} (attempt {attempt + 1}/3)')
            pull_output = client.pull(image)
            # Handle the output which might be bytes or string
            if pull_output:
                if isinstance(pull_output, bytes):
                    for line in pull_output.splitlines():
                        logger.debug(line.decode())
                elif isinstance(pull_output, str):
                    for line in pull_output.splitlines():
                        logger.debug(line)
            break
        except DockerException as e:
            logger.error(f'failed to pull Docker image (attempt {attempt + 1}/3): {e}')
            if attempt == 2:  # Last attempt failed
                message = f'failed to pull Docker image after 3 attempts: {e}'
                logger.error(message)
                pytest.exit(message)
            time.sleep(5)  # Wait before retry

    # Create the container with retries
    for attempt in range(1, 4):
        try:
            logger.info(f'creating container {container_name} (attempt {attempt}/3)')
            container = client.create_container(image, **config)
            return container
        except DockerException as e:
            logger.error(f'failed to create container (attempt {attempt}/3): {e}')
            # Try to clean up on the last attempt
            if attempt == 3:  # Last attempt failed
                message = f'failed to create Docker container after 3 attempts: {e}'
                logger.error(message)
                pytest.exit(message)

            with contextlib.suppress(DockerException):
                client.remove_container(container=container_name, force=True)

            time.sleep(3)  # Wait before retry


def create_postgres_docker_container(client: docker.APIClient):
    """Create a Postgres Docker container for testing.

    Args:
        client: Docker API client

    Returns:
        Created Postgres container
    """
    postgres_container_config = dict(
        image='postgres:16',
        name='postgres_testing',
        environment={
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'postgres',
            'POSTGRES_DB': 'ichrisbirch',
        },
        ports=[5432],
        # Bind to port 5434 on host machine, so that it doesn't conflict with local Postgres
        host_config=client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
        detach=True,
        labels=['testing'],
    )
    return create_docker_container(client=client, config=postgres_container_config)


def docker_logs(client: docker.APIClient, container_id: str):
    """Stream Docker container logs to the Python logger.

    Args:
        client: Docker API client
        container_id: ID of the container to stream logs from
    """
    docker_logger = logging.getLogger('DOCKER')
    for log in client.logs(container=container_id, stream=True, follow=True):
        # Handle log which might be bytes or string
        if isinstance(log, bytes):
            log_str = log.decode('utf-8', errors='replace').strip()
        else:
            log_str = str(log).strip()
        docker_logger.debug(log_str)
