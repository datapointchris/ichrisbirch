import logging
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
from sqlalchemy.sql import select
from sqlalchemy.sql import text

import tests.test_data
import tests.test_data.habitcategories
import tests.test_data.habitscompleted
from ichrisbirch import models
from ichrisbirch.config import get_settings

logger = logging.getLogger('tests.util')
logger.info('testing util loaded')
settings = get_settings()

# NOTE: These have to be dicts, if they are models.User objects, they will be incorrect
# when called after the first module that uses them because they will change somehow (sqlalchemy bullshit magic)
# Sacrificial test user is inserted first, deleted for testing, so as not to delete the login users
SACRIFICIAL_TEST_USER = dict(
    name='User to be Sacrificed to Testing Gods', email='sacrifice@testgods.com', password='repentance'
)
TEST_LOGIN_REGULAR_USER = dict(
    name='Test Login Regular User', email='testregular@testuser.com', password='regularpassword'
)
TEST_LOGIN_ADMIN_USER = dict(
    name='Test Login Admin User', email='testadmin@testadmin.com', password='adminpassword', is_admin=True
)
TEST_LOGIN_API_REGULAR_USER = dict(
    name='Test Login API Regular User', email='testregularapi@testuser.com', password='regularpassword'
)
TEST_LOGIN_API_ADMIN_USER = dict(
    name='Test Login API Admin User', email='testadminapi@testadmin.com', password='adminpassword', is_admin=True
)
TEST_SERVICE_ACCOUNT_USER = dict(
    name=settings.users.service_account_user_name,
    email=settings.users.service_account_user_email,
    password=settings.users.service_account_user_password,
)


ENGINE = create_engine(
    settings.sqlalchemy.db_uri,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=5,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)
SessionTesting = sessionmaker(bind=ENGINE, autocommit=False, autoflush=True, expire_on_commit=False)


def get_testing_session() -> Generator[Session, None, None]:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def get_test_user(user_dict: dict):
    with SessionTesting() as session:
        return session.execute(select(models.User).where(models.User.email == user_dict['email'])).scalar_one()


def insert_test_data(*datasets):
    """Insert testing data for each endpoint.

    The data is manually added, must update when a new endpoint is added.
    deepcopy(data) is necessary or the tests will mutate the BASE_DATA
    and cause test failures

    Get only the data needed for each endpoint, speeds up tests a bunch.
    The tradeoff is a fixture must be created in each testing file

    Example (put at the top of each file using the testing data):

    ```python
    import tests.util


    @pytest.fixture(autouse=True)
    def insert_testing_data():
        insert_test_data("tasks")
    ```
    """
    base_datasets = {
        'articles': tests.test_data.articles.BASE_DATA,
        'autotasks': tests.test_data.autotasks.BASE_DATA,
        'boxes': tests.test_data.boxes.BASE_DATA,
        'boxitems': tests.test_data.boxitems.BASE_DATA,
        'countdowns': tests.test_data.countdowns.BASE_DATA,
        'events': tests.test_data.events.BASE_DATA,
        'habitcategories': tests.test_data.habitcategories.BASE_DATA,
        'habits': tests.test_data.habits.BASE_DATA,
        'habitscompleted': tests.test_data.habitscompleted.BASE_DATA,
        'money_wasted': tests.test_data.money_wasted.BASE_DATA,
        'tasks': tests.test_data.tasks.BASE_DATA,
        'users': tests.test_data.users.BASE_DATA,
    }
    selected_datasets = [deepcopy(base_datasets[key]) for key in datasets if key in base_datasets]
    with SessionTesting() as session:
        for data in selected_datasets:
            session.add_all(data)
        session.commit()
    logger.info(f'inserted testing dataset: {' '.join(f"'{d}'" for d in datasets)}')


def delete_test_data(*datasets):
    table_models = {
        'articles': models.Article,
        'autotasks': models.AutoTask,
        'boxes': models.Box,
        'boxitems': models.BoxItem,
        'countdowns': models.Countdown,
        'events': models.Event,
        'habitcategories': models.HabitCategory,
        'habits': models.Habit,
        'habitscompleted': models.HabitCompleted,
        'money_wasted': models.MoneyWasted,
        'tasks': models.Task,
        'users': models.User,
    }
    with SessionTesting() as session:
        for table in datasets:
            table_model = table_models[table]
            if 'users' in table:
                dont_delete_login_users = table_model.email.notin_(
                    [TEST_LOGIN_REGULAR_USER['email'], TEST_LOGIN_ADMIN_USER['email']]
                )
                all_table_items = session.execute(select(table_model).where(dont_delete_login_users)).scalars().all()
            else:
                all_table_items = session.execute(select(table_model)).scalars().all()
            for item in all_table_items:
                session.delete(item)
            if table_model.__table__.schema is not None:
                table_name = f"{table_model.__table__.schema}.{table_model.__table__.name}"
            else:
                table_name = table_model.__table__.name
            if 'users' not in table:
                session.execute(text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1"))
                logger.info(f'reset sequence for {table_name}')
        session.commit()
    logger.info(f'deleted testing dataset: {' '.join(f"'{d}'" for d in datasets)}')


def log_all_table_items(table_name, model, model_attribute=None):
    with SessionTesting() as session:
        all_table_items = session.execute(select(model)).scalars().all()
        items = [getattr(item, model_attribute) if model_attribute else item for item in all_table_items]
        logger.warning(f'ALL {table_name.upper()}: {', '.join(items)}')


def show_status_and_response(response: httpx.Response) -> dict[str, str]:
    """Convert status code to description and return response if any."""
    d = {}
    for attr in dir(status):
        code = attr.split('_')[1]
        d[int(code)] = attr
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError) as e:
        logger.warning(f'error decoding response content: {e}')
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}


def get_docker_client(logger: logging.Logger) -> docker.APIClient:
    try:
        return docker.APIClient(base_url='unix://var/run/docker.sock')
    except DockerException:
        logger.warning('docker is not running, starting...')
        subprocess.run(['open', '-ga', 'docker'])
        subprocess.run(['sleep', '20'])
        logger.info('docker started')
        # Try again, let failure surface in the next command if this was not the issue
        return docker.APIClient(base_url='unix://var/run/docker.sock')


def create_docker_container(client: docker.APIClient, config: dict[str, Any]) -> Container:
    image = config.pop("image")
    try:
        client.pull(image)
        container = client.create_container(image, **config)
    except DockerException as e:
        message = f"Failed to CREATE Docker container: {e}"
        logger.error(message)
        try:
            client.remove_container(container=config.get("name"), force=True)
            container = client.create_container(image, **config)
        except DockerException as e:
            message = f"Failed to REMOVE and RECREATE Docker container: {e}"
            logger.error(message)
            pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    return container


def create_postgres_docker_container(client: docker.APIClient):
    postgres_container_config = dict(
        image='postgres:16',
        name='postgres_testing',
        environment={
            'ENVIRONMENT': settings.ENVIRONMENT,
            'POSTGRES_USER': settings.postgres.username,
            'POSTGRES_PASSWORD': settings.postgres.password,
            'POSTGRES_DB': settings.postgres.database,
        },
        ports=[5432],
        # Bind to port 5434 on host machine, so that it doesn't conflict with local Postgres
        host_config=client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
        detach=True,
        labels=['testing'],
    )
    postgres_container = create_docker_container(client=client, config=postgres_container_config)
    return postgres_container


def docker_logs(client: docker.APIClient, container_id: str):
    docker_logger = logging.getLogger('DOCKER')
    for log in client.logs(container=container_id, stream=True, follow=True):
        log = log.decode().strip()
        docker_logger.debug(log)
