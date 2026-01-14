"""Test environment management for running tests with Docker, FastAPI, and Flask.

This module handles the setup and teardown of the test environment, including:
- Docker container management for Postgres
- Starting and stopping API and App servers
- Creating test clients for API and App
- Docker Compose-based test environment setup
"""

import json
import logging
import os
import socket
import subprocess

# import threading
import time

# import docker
import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.schema import CreateSchema

from ichrisbirch import models
from ichrisbirch.config import Settings
from ichrisbirch.database.base import Base
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import get_test_login_users

# from ichrisbirch.config import settings
# from ichrisbirch.database.models.session import create_session
# from tests.utils.docker import create_postgres_docker_container
# from tests.utils.docker import docker_logs
# from tests.utils.docker import get_docker_client

logger = logging.getLogger(__name__)


class DockerComposeTestEnvironment:
    """Context manager for Docker Compose-based test environment.

    This is the new preferred approach that:
    - Uses Docker Compose to start test services
    - Services use ENVIRONMENT=testing for test-specific configuration
    - Runs on different ports to avoid conflicts with dev environment
    - Allows pytest to run locally against containerized services

    In CI, containers are pre-started by the workflow, so we only verify they're running.
    """

    # CI uses an additional override file for CI-specific configuration
    COMPOSE_FILES = '-f docker-compose.yml -f docker-compose.test.yml'
    COMPOSE_FILES_CI = '-f docker-compose.yml -f docker-compose.test.yml -f docker-compose.ci.yml'
    COMPOSE_COMMAND = f'docker compose --project-name ichrisbirch-test {COMPOSE_FILES} up -d'
    COMPOSE_COMMAND_CI = f'docker compose --project-name ichrisbirch-test {COMPOSE_FILES_CI} up -d'

    @property
    def is_ci(self) -> bool:
        """Detect if running in CI environment."""
        return os.environ.get('CI', '').lower() == 'true'

    def __init__(self, settings: Settings, test_session_generator):
        self.settings = settings
        self.test_session_generator = test_session_generator
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
        Locally: always do full cleanup and start fresh to avoid race conditions.
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
                # Always do full cleanup first (handles race conditions from back-to-back runs)
                logger.info('Cleaning up any existing test containers...')
                self.stop_docker_compose()
                time.sleep(3)  # Wait for volumes/networks to be fully released
                logger.info('Starting fresh Docker Compose test services')
                self.setup_test_services()

            # Ensure database is ready
            self.ensure_database_ready()

        except Exception as e:
            logger.error(f'Error during setup: {e}')
            if not self.is_ci:
                self.teardown()
            pytest.exit(f'Exiting due to setup failure: {e}', returncode=1)

    def teardown(self) -> None:
        if self.is_ci:
            logger.info('Skipping Docker Compose teardown in CI - handled by workflow')
            return
        logger.info('Tearing down Docker Compose test environment')
        self.stop_docker_compose()

    def docker_test_services_already_running(self, required_services=None) -> bool:
        """Returns True if all required Docker Compose services are running."""
        if required_services is None:
            required_services = {'postgres', 'redis', 'api', 'app', 'chat'}
        try:
            # Use docker ps with JSON format for clean parsing
            cmd = ['docker', 'ps', '--filter', 'status=running', '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.warning(f'docker ps failed: {result.stderr}')
                return False

            # Parse JSON output and extract running test services
            running_services = {
                json.loads(line).get('Names', '').removeprefix('ichrisbirch-').removesuffix('-testing')
                for line in result.stdout.strip().splitlines()
                if line.strip() and 'ichrisbirch-' in line and '-testing' in line
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
                self._log_container_debug_info(f'ichrisbirch-{service_name}-testing')
                raise RuntimeError(f'{service_name} on {host}:{port} did not respond after {max_attempts * 5} seconds')

        http_services = {
            'api': f'{self.settings.api_url}/health',
            'app': f'{self.settings.protocol}://{self.settings.flask.host}:{self.settings.flask.port}',
            'chat': f'{self.settings.protocol}://{self.settings.chat.host}:{self.settings.chat.port}',
        }
        for service_name, url in http_services.items():
            logger.info(f'Checking {service_name} readiness at {url}')
            attempts = 0
            max_attempts = 6  # Increased from 6 to allow 60 seconds total
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
                self._log_container_debug_info(f'ichrisbirch-{service_name}-testing')
                raise RuntimeError(f'{service_name} on url {url} did not respond after {max_attempts * 5} seconds')

    def create_database_schemas(self) -> None:
        """Create database schemas (idempotent - uses IF NOT EXISTS)."""
        with self.test_session_generator(self.settings) as session:
            for schema_name in self.settings.postgres.db_schemas:
                try:
                    session.execute(CreateSchema(schema_name, if_not_exists=True))
                    logger.info(f'Ensured schema exists: {schema_name}')
                except Exception as e:
                    logger.error(f'Failed to create schema {schema_name}: {e}')
                    raise
            session.commit()

    def ensure_database_ready(self) -> None:
        """Ensure database is in a known good state (idempotent).

        This runs whether services were just started or already running.
        It ensures:
        1. Schemas exist
        2. Tables exist
        3. Login users exist

        All operations are idempotent - safe to run multiple times.
        """
        # 1. Create schemas (idempotent via IF NOT EXISTS)
        self.create_database_schemas()

        # 2. Create tables (idempotent via checkfirst=True)
        engine = get_db_engine(self.settings)
        Base.metadata.create_all(engine, checkfirst=True)
        logger.info('Ensured all tables exist')

        # 3. Ensure login users exist (check before insert)
        with self.test_session_generator(self.settings) as session:
            for user_data in get_test_login_users():
                existing = session.execute(select(models.User).where(models.User.email == user_data['email'])).scalar_one_or_none()
                if not existing:
                    session.add(models.User(**user_data))
                    logger.info(f'Inserted login user: {user_data["email"]}')
                else:
                    logger.debug(f'Login user already exists: {user_data["email"]}')
            session.commit()
        logger.info('Database is ready')

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
                'ichrisbirch-test',
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
            services = ['postgres', 'redis', 'api', 'app', 'chat', 'scheduler', 'traefik']
            containers = [f'ichrisbirch-{s}-testing' for s in services]
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


# class TestEnvironment:
#     """Container class for test environment configuration and resources."""

#     def __init__(self, settings):
#         self.settings = settings
#         self.postgres_container_id: Optional[str] = None
#         self.threads: dict[str, threading.Thread] = {}
#         self.api_process: Optional[subprocess.Popen] = None
#         self.app_process: Optional[subprocess.Popen] = None
#         self.docker_client: Optional[docker.APIClient] = None
#         self.docker_compose_process: Optional[subprocess.Popen] = None

#     def __enter__(self):
#         """Context manager entry - setup the environment."""
#         self.setup()
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit - always teardown the environment."""
#         self.teardown()
#         if exc_type is not None:
#             logger.error(f'Exception during context: {exc_type.__name__}: {exc_val}')
#         return False  # Don't suppress exceptions

#     def setup(self):
#         try:
#             # self.setup_docker_and_postgres()
#             self.create_database_schemas()
#             # self.start_fastapi_server()
#             # self.start_flask_app_server()
#         except Exception as e:
#             logger.error(f'Error during setup: {e}')
#             self.teardown()
#             raise

#     def setup_docker_and_postgres(self) -> None:
#         def start_postgres_container():
#             try:
#                 self.docker_client.start(container=self.postgres_container_id)
#             except Exception as e:
#                 logger.error(f'Error starting Postgres container: {e}')
#                 raise

#         try:
#             self.docker_client = get_docker_client(logger=logger)
#             postgres_container = create_postgres_docker_container(client=self.docker_client)
#             self.postgres_container_id = postgres_container.get('Id')
#             logger.info(f'Created Postgres container')

#             postgres_thread = threading.Thread(target=start_postgres_container, name='postgres_thread')
#             postgres_thread.daemon = True
#             postgres_thread.start()
#             self.threads['postgres_thread'] = postgres_thread
#             time.sleep(5)
#             logger.info('Postgres container started successfully')

#             logger.info('Starting Docker log stream')
#             docker_log_thread = threading.Thread(
#                 target=docker_logs,
#                 kwargs={
#                     'client': self.docker_client,
#                     'container_id': self.postgres_container_id,
#                 },
#                 name='docker_log_thread',
#             )
#             docker_log_thread.daemon = True
#             docker_log_thread.start()
#             self.threads['docker_log_thread'] = docker_log_thread
#             logger.info('Docker log stream started successfully')
#         except Exception as e:
#             logger.error(f'Error setting up Docker and Postgres: {e}')
#             raise

#     def create_database_schemas(self) -> None:
#         with create_session() as session:
#             for schema_name in self.settings.postgres.db_schemas:
#                 try:
#                     session.execute(CreateSchema(schema_name))
#                     logger.info(f'Created schema: {schema_name}')
#                 except Exception as e:
#                     logger.error(f'Failed to create schema {schema_name}: {e}')
#                     raise
#             session.commit()

#     def start_fastapi_server(self):
#         logger.info('Starting FastAPI server')
#         command = ['poetry', 'run', 'uvicorn', 'tests.wsgi_api:api']
#         args = [
#             '--host',
#             self.settings.fastapi.host,
#             '--port',
#             str(self.settings.fastapi.port),
#             '--log-level',
#             'debug',
#             '--reload-exclude',
#             '*',
#         ]
#         self.api_process = subprocess.Popen(
#             command + args,
#             env=os.environ,
#             stdout=None,
#             stderr=subprocess.PIPE,
#             text=True,
#             bufsize=1,
#         )
#         time.sleep(5)  # Wait for the server to start
#         try:
#             response = httpx.get(self.settings.api_url, follow_redirects=True)
#             if response.status_code != 200:
#                 logger.error(f'FastAPI server returned status {response.status_code}')
#                 raise RuntimeError
#         except Exception as e:
#             logger.error(f'Error checking FastAPI server status: {e}')
#             self.api_process.kill()
#             self.api_process.wait()
#             if self.api_process.stderr and (stderr_output := self.api_process.stderr.read()):
#                 error_logger = logging.getLogger('FASTAPI_TEST_SERVER')
#                 for line in stderr_output.strip().split('\n'):
#                     if line.strip().startswith('ERROR:'):
#                         error_logger.error(line.strip())
#             raise
#         logger.info(f'FastAPI server process started on {self.settings.fastapi.host}:{self.settings.fastapi.port}')

#     def start_flask_app_server(self) -> None:
#         """Start the Flask app server with proper error handling."""
#         logger.info('Starting Flask app server')
#         flask_uri = f'{self.settings.flask.host}:{self.settings.flask.port}'
#         command = ['poetry', 'run', 'gunicorn', 'tests.wsgi_app:app']
#         args = ['--bind', flask_uri, '--log-level', 'DEBUG']
#         self.app_process = subprocess.Popen(
#             command + args,
#             env=os.environ,
#             stdout=None,
#             stderr=subprocess.PIPE,
#             text=True,
#             bufsize=1,
#         )
#         time.sleep(4)
#         url = f'{self.settings.protocol}://{flask_uri}'
#         try:
#             response = httpx.get(url, timeout=5)
#             if response.status_code != 200:
#                 logger.error(f'Flask server returned status {response.status_code}')
#                 raise RuntimeError
#         except Exception as e:
#             logger.error(f'Error checking Flask server status: {e}')
#             self.app_process.kill()
#             self.app_process.wait()
#             if self.app_process.stderr and (stderr_output := self.app_process.stderr.read()):
#                 error_logger = logging.getLogger('FLASK_TEST_SERVER')
#                 for line in stderr_output.strip().split('\n'):
#                     if line.strip().startswith('ERROR:'):
#                         error_logger.error(line.strip())
#             raise
#         logger.info(f'Flask server process started on {flask_uri}')

#     def stop_process(self, process: subprocess.Popen | None) -> None:
#         if process:
#             try:
#                 process.kill()
#                 process.wait()
#                 logger.info(f'killed {str(process.args).split("--")[0]}')
#             except Exception as e:
#                 logger.warning(f'Error stopping {process} process: {e}')

#     def stop_docker_container(self) -> None:
#         if self.docker_client and self.postgres_container_id:
#             try:
#                 self.docker_client.stop(container=self.postgres_container_id)
#                 logger.info('Postgres container stopped')
#             except Exception as e:
#                 logger.warning(f'Error stopping Postgres container: {e}')

#     def join_threads(self) -> None:
#         for _thread_name, thread in self.threads.items():
#             thread.join()

#     def teardown(self) -> None:
#         self.stop_process(self.api_process)
#         self.stop_process(self.app_process)
#         self.stop_docker_container()
#         self.stop_docker_compose()
#         self.join_threads()

#     def stop_docker_compose(self) -> None:
#         """Stop Docker Compose services - placeholder for compatibility."""
#         if self.docker_compose_process:
#             try:
#                 self.docker_compose_process.terminate()
#                 self.docker_compose_process.wait()
#                 logger.info('Stopped Docker Compose process')
#             except Exception as e:
#                 logger.warning(f'Error stopping Docker Compose process: {e}')
