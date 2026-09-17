"""The Docker Compose test environment a pytest session runs against.

`DockerComposeTestEnvironment` starts the test containers or reuses running
ones, waits for Postgres, Redis and the API, and initializes the database.
Resetting the data between sessions is the `truncate_tables` fixture's job.
"""

import json
import logging
import os
import socket
import subprocess
import time

import httpx
import pytest

from ichrisbirch.config import Settings
from ichrisbirch.database.initialization import full_initialization

logger = logging.getLogger(__name__)


class DockerComposeTestEnvironment:
    """Context manager for the Docker Compose test environment.

    It:
    - Uses Docker Compose to start test services
    - Services use ENVIRONMENT=testing for test-specific configuration
    - Runs on different ports to avoid conflicts with dev environment
    - Allows pytest to run locally against containerized services

    In CI, containers are pre-started by the workflow, so we only verify they're running.
    """

    # CI uses an additional override file for CI-specific configuration
    COMPOSE_FILES = '-f docker-compose.yml -f docker-compose.test.yml'
    COMPOSE_FILES_CI = '-f docker-compose.yml -f docker-compose.test.yml -f docker-compose.ci.yml'
    COMPOSE_COMMAND = f'docker compose --project-name icb-test {COMPOSE_FILES} up -d'
    COMPOSE_COMMAND_CI = f'docker compose --project-name icb-test {COMPOSE_FILES_CI} up -d'

    @property
    def is_ci(self) -> bool:
        """Detect if running in CI environment."""
        return os.environ.get('CI', '').lower() == 'true'

    def __init__(self, settings: Settings):
        self.settings = settings
        self.docker_compose_process: subprocess.Popen | None = None

    def __enter__(self):
        """Context manager entry - setup the Docker Compose test environment."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - always teardown the environment."""
        self.teardown()
        if exc_type is not None:
            logger.error(f'Exception during context: {exc_type.__name__}: {exc_val}')
        return False  # Don't suppress exceptions

    def setup(self):
        """Setup the Docker Compose test environment.

        In CI: containers are pre-started by workflow, just wait for them.
        Locally: reuse running containers for fast iteration, start if needed.
        Then bring the database to the current schema.
        """
        try:
            if self.is_ci:
                logger.info('Running in CI environment - containers should be pre-started by workflow')
                if not self.docker_test_services_already_running():
                    logger.warning('CI containers not detected, waiting for them to start...')
                    time.sleep(10)
                    if not self.docker_test_services_already_running():
                        raise RuntimeError('CI containers not running - check workflow configuration')
                logger.info('CI containers detected and running')
            else:
                # Check if containers are already running
                if self.docker_test_services_already_running():
                    logger.info('Test containers already running, reusing them')
                    self.verify_test_services()
                else:
                    logger.info('Starting Docker Compose test services')
                    self.setup_test_services()

            # Healthy containers can hold an empty database: the test Postgres
            # keeps its data on tmpfs, so every recreate of it starts blank.
            # Initialization is idempotent and leaves an initialized database
            # unchanged.
            full_initialization(self.settings)

        except Exception as e:
            logger.error(f'Error during setup: {e}')
            pytest.exit(f'Exiting due to setup failure: {e}', returncode=1)

    def teardown(self) -> None:
        """Leave containers running for fast iteration."""
        logger.info('Leaving test containers running for fast iteration')
        logger.info('Stop manually with: icbops testing stop')

    def docker_test_services_already_running(self, required_services=None) -> bool:
        """Returns True if all required Docker Compose services are running."""
        if required_services is None:
            required_services = {'postgres', 'redis', 'api'}
        try:
            # Use docker ps with JSON format for clean parsing
            cmd = ['docker', 'ps', '--filter', 'status=running', '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.warning(f'docker ps failed: {result.stderr}')
                return False

            # Parse JSON output and extract running test services
            running_services = {
                json.loads(line).get('Names', '').removeprefix('icb-test-')
                for line in result.stdout.strip().splitlines()
                if line.strip() and 'icb-test-' in line
            }

            # Check if all required services are running
            return required_services.issubset(running_services)
        except Exception as e:
            logger.error(f'Error checking Docker Compose services: {e}')
            return False

    def setup_test_services(self) -> None:
        """Start Docker Compose test services."""
        logger.info('Starting Docker Compose test services')
        try:
            result = subprocess.run(self.COMPOSE_COMMAND.split(' '), capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                logger.error(f'Docker Compose failed with return code {result.returncode}')
                logger.error(f'STDOUT: {result.stdout}')
                logger.error(f'STDERR: {result.stderr}')
                raise RuntimeError('Failed to start Docker Compose test environment')

            logger.info('Docker Compose test services started successfully')
            logger.info('Waiting for services to be ready...')
            time.sleep(10)
            self.verify_test_services()

        except subprocess.TimeoutExpired as e:
            logger.error('Docker Compose startup timed out')
            raise RuntimeError('Docker Compose test environment startup timed out') from e

    def verify_test_services(self) -> None:
        """Verify that test services are responding on their test ports."""
        # These should match the test ports configured in docker-compose.test.yml
        test_services = {
            'postgres': (self.settings.postgres.host, self.settings.postgres.port),
            'redis': (self.settings.redis.host, self.settings.redis.port),
        }
        for service_name, (host, port) in test_services.items():
            logger.info(f'Checking {service_name} readiness on {host}:{port}')
            attempts = 0
            max_attempts = 6
            service_running = False
            while not service_running and attempts < max_attempts:
                try:
                    with socket.create_connection((host, port), timeout=5):
                        service_running = True
                        logger.info(f'{service_name} is responding on {host}:{port}')
                        break
                except (OSError, TimeoutError) as e:
                    logger.error(f'Attempt {attempts + 1}/{max_attempts} - {service_name} not responding on {host}:{port}: {e}')
                attempts += 1
                time.sleep(5)
            if attempts >= max_attempts:
                self._log_container_debug_info(f'icb-test-{service_name}')
                raise RuntimeError(f'{service_name} on {host}:{port} did not respond after {max_attempts * 5} seconds')

        http_services = {
            'api': f'{self.settings.api_url}/health',
        }
        for service_name, url in http_services.items():
            logger.info(f'Checking {service_name} readiness at {url}')
            attempts = 0
            max_attempts = 6
            service_running = False
            while not service_running and attempts < max_attempts:
                try:
                    response = httpx.get(url, timeout=5).raise_for_status()
                    if service_running := response.status_code == 200:
                        logger.info(f'{service_name} is ready at {url}')
                        break
                    else:
                        logger.warning(f'{service_name} returned status {response.status_code} at {url}')
                except httpx.RequestError as e:
                    logger.error(f'Error connecting to {service_name} at {url}: {e}')
                attempts += 1
                time.sleep(5)
            if attempts >= max_attempts:
                self._log_container_debug_info(f'icb-test-{service_name}')
                raise RuntimeError(f'{service_name} on url {url} did not respond after {max_attempts * 5} seconds')

    def stop_docker_compose(self) -> None:
        """Stop Docker Compose test services completely.

        Always uses --volumes --remove-orphans to ensure clean state for next run.
        """
        logger.info('Stopping Docker Compose test services (with volumes cleanup)...')
        try:
            cmd = [
                'docker',
                'compose',
                '--project-name',
                'icb-test',
                '-f',
                'docker-compose.yml',
                '-f',
                'docker-compose.test.yml',
                'down',
                '--volumes',
                '--remove-orphans',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                logger.info('Docker Compose test services stopped successfully')
            else:
                logger.warning(f'Docker Compose down had issues: {result.stderr}')

        except subprocess.TimeoutExpired:
            logger.warning('Docker Compose down timed out, forcing container removal')
            # Force kill any remaining containers
            services = ['postgres', 'redis', 'api', 'scheduler', 'traefik']
            containers = [f'icb-test-{s}' for s in services]
            subprocess.run(['docker', 'rm', '-f'] + containers, capture_output=True, timeout=30)
        except Exception as e:
            logger.warning(f'Error stopping Docker Compose: {e}')

    def _log_container_debug_info(self, container_name: str) -> None:
        """Log container status and logs for debugging failed services."""
        try:
            # Check container status
            status_cmd = ['docker', 'inspect', container_name, '--format', '{{.State.Status}}']
            status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
            if status_result.returncode == 0:
                logger.error(f'Container {container_name} status: {status_result.stdout.strip()}')

            # Get container logs (last 50 lines)
            logs_cmd = ['docker', 'logs', '--tail', '50', container_name]
            logs_result = subprocess.run(logs_cmd, capture_output=True, text=True, timeout=10)
            if logs_result.returncode == 0:
                logger.error(f'Container {container_name} logs:\n{logs_result.stdout}')
                if logs_result.stderr:
                    logger.error(f'Container {container_name} stderr:\n{logs_result.stderr}')
            else:
                logger.error(f'Failed to get logs for {container_name}: {logs_result.stderr}')

        except Exception as e:
            logger.error(f'Error getting debug info for {container_name}: {e}')
