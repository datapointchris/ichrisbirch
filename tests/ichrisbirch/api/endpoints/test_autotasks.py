import logging

import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('autotasks')
    yield
    tests.util.delete_test_data('autotasks')


NEW_OBJ = schemas.AutoTaskCreate(
    name='AutoTask 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
    frequency=AutoTaskFrequency.Biweekly,
)

ENDPOINT = '/autotasks/'

crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api):
    crud_tests.test_read_one(test_api)


def test_read_many(test_api):
    crud_tests.test_read_many(test_api)


def test_create(test_api):
    crud_tests.test_create(test_api)


def test_delete(test_api):
    crud_tests.test_delete(test_api)


def test_lifecycle(test_api):
    crud_tests.test_lifecycle(test_api)


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(test_api, category):
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
        frequency=AutoTaskFrequency.Biweekly,
    )
    created = test_api.post(ENDPOINT, json=test_obj.model_dump())
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name


@pytest.mark.parametrize('frequency', list(AutoTaskFrequency))
def test_task_frequencies(test_api, frequency):
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=TaskCategory.Personal,
        priority=3,
        frequency=frequency,
    )
    created = test_api.post(ENDPOINT, json=test_obj.model_dump())
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name
