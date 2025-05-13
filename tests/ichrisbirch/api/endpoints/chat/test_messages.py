import pytest

import tests.util
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data
from ichrisbirch import schemas
from tests.test_data.chats import BASE_DATA

from ..crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('chats')
    yield
    delete_test_data('chats')


ENDPOINT = '/chat/messages/'
NEW_OBJ = schemas.ChatMessageCreate(
    chat_id=1,
    role="user",
    content="Why am I not independently wealthy yet?",
)

NUM_TEST_CHAT_MESSAGES = sum([len(chat.messages) for chat in BASE_DATA])

crud_tests = ApiCrudTester(
    endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='content', expected_length=NUM_TEST_CHAT_MESSAGES
)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in)


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in)
