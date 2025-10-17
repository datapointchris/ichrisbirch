"""Test environment management for running tests with Docker, FastAPI, and Flask.

This module handles the setup and teardown of the test environment, including:
- Docker container management for Postgres
- Starting and stopping API and App servers
- Creating test clients for API and App
- Docker Compose-based test environment setup
"""

import json
import logging
import socket
import subprocess

# import threading
import time

# import docker
import httpx
import pytest

# from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import Settings

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
    """

    COMPOSE_COMMAND = 'docker compose --project-name ichrisbirch-testing -f docker-compose.yml -f docker-compose.test.yml up -d'

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
        """Setup the Docker Compose test environment."""
        try:
            if not self.docker_test_services_already_running():
                logger.info('Docker Compose test services not running, starting them up')
                self.setup_test_services()
                self.create_database_schemas()
            else:
                logger.info('Docker Compose test services already running, skipping setup')
        except Exception as e:
            logger.error(f'Error during setup: {e}')
            self.teardown()
            pytest.exit(f'Exiting due to setup failure: {e}', returncode=1)

    def teardown(self) -> None:
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
        # self.stop_docker_compose()
        logger.info('Starting Docker Compose test services')
        try:
            result = subprocess.run(self.COMPOSE_COMMAND.split(' '), capture_output=True, text=True, timeout=60)

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
        except Exception as e:
            logger.error(f'Error setting up Docker Compose test environment: {e}')
            # self.stop_docker_compose()
            raise

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
                raise RuntimeError(f'{service_name} on {host}:{port} did not respond after {max_attempts * 5} seconds')

        http_services = {
            'api': f'{self.settings.api_url}/health',
            'app': f'{self.settings.protocol}://{self.settings.flask.host}:{self.settings.flask.port}',
            'chat': f'{self.settings.protocol}://{self.settings.chat.host}:{self.settings.chat.port}',
        }
        for service_name, url in http_services.items():
            logger.info(f'Checking {service_name} readiness at {url}')
            attempts = 0
            max_attempts = 12  # Increased from 6 to allow 60 seconds total
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
                raise RuntimeError(f'{service_name} on url {url} did not respond after {max_attempts * 5} seconds')

    def create_database_schemas(self):
        with self.test_session_generator(self.settings) as session:
            for schema_name in self.settings.postgres.db_schemas:
                try:
                    session.execute(CreateSchema(schema_name))
                    logger.info(f'Created schema: {schema_name}')
                except Exception as e:
                    logger.error(f'Failed to create schema {schema_name}: {e}')
                    raise
            session.commit()

    def stop_docker_compose(self) -> None:
        try:
            # test_env = os.environ.copy()
            # test_env.update(
            #     {
            #         'POSTGRES_PORT': '5434',
            #         'REDIS_PORT': '6380',
            #         'FASTAPI_PORT': '8001',
            #         'FLASK_PORT': '5001',
            #         'CHAT_PORT': '8507',
            #         'ENVIRONMENT': 'testing',
            #     }
            # )
            cmd = 'docker compose --project-name ichrisbirch-testing -f docker-compose.yml -f docker-compose.test.yml down'
            result = subprocess.run(cmd.split(' '), capture_output=True, text=True, timeout=120)
            # result = subprocess.run(cmd.split(' '), env=test_env, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                logger.info('Docker Compose test services stopped successfully')
            else:
                logger.warning(f'Docker Compose down had issues: {result.stderr}')

        except subprocess.TimeoutExpired:
            logger.warning('Docker Compose down timed out, forcing cleanup')
            force_command = [
                'docker-compose',
                '--project-name',
                'ichrisbirch-testing',
                '-f',
                'docker-compose.yml',
                '-f',
                'docker-compose.test.yml',
                'down',
                '--volumes',
                '--remove-orphans',
            ]
            subprocess.run(force_command, capture_output=True, timeout=30)
            # subprocess.run(force_command, env=test_env, capture_output=True, timeout=30)
        except Exception as e:
            logger.warning(f'Error stopping Docker Compose: {e}')


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
