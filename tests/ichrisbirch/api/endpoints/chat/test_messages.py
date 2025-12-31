import pytest

from ichrisbirch import schemas
from tests.factories import ChatFactory
from tests.factories import ChatMessageFactory

from ..crud_test import ApiCrudTester

ENDPOINT = '/chat/messages/'
NUM_TEST_CHATS = 3
MESSAGES_PER_CHAT = 2
NUM_TEST_MESSAGES = NUM_TEST_CHATS * MESSAGES_PER_CHAT


@pytest.fixture
def message_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data using factories."""
    client, session = txn_api_logged_in

    # Create chats with messages using factories
    chats = ChatFactory.create_batch(NUM_TEST_CHATS)
    for chat in chats:
        ChatMessageFactory.create_batch(MESSAGES_PER_CHAT, chat=chat)

    # Use first chat for new message creation
    first_chat = chats[0]
    new_obj = schemas.ChatMessageCreate(
        chat_id=first_chat.id,
        role='user',
        content='Why am I not independently wealthy yet?',
    )
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=new_obj, verify_attr='content', expected_length=NUM_TEST_MESSAGES)
    return client, crud_tester


def test_read_one(message_crud_tester):
    client, crud_tester = message_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(message_crud_tester):
    client, crud_tester = message_crud_tester
    crud_tester.test_read_many(client)


def test_create(message_crud_tester):
    client, crud_tester = message_crud_tester
    crud_tester.test_create(client)


def test_delete(message_crud_tester):
    client, crud_tester = message_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(message_crud_tester):
    client, crud_tester = message_crud_tester
    crud_tester.test_lifecycle(client)
