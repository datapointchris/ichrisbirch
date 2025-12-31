import pytest

from ichrisbirch import schemas
from tests.factories import ChatFactory

from ..crud_test import ApiCrudTester

ENDPOINT = '/chat/chats/'
NUM_TEST_CHATS = 3
NEW_OBJ = schemas.ChatCreate(
    name='Chat 4 Computer with notes priority 3',
    category='AWS',
    subcategory='Lambda',
    tags=['cloud', 'aws'],
    messages=[
        schemas.ChatMessageCreate(role='assistant', content='Hello, how can I help you today?'),
        schemas.ChatMessageCreate(role='user', content='Help me with setting up AWS Lambda SAM'),
        schemas.ChatMessageCreate(
            role='assistant',
            content="""AWS Lambda is a serverless compute service that lets you run code without provisioning or managing servers.

                    You can use AWS Lambda to run code for virtually any type of application or backend service with zero administration.
                    Just upload your code and Lambda takes care of everything required to run and scale your code with high availability.
                    """,
        ),
    ],
)


@pytest.fixture
def chat_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data using factories."""
    client, session = txn_api_logged_in
    ChatFactory.create_batch(NUM_TEST_CHATS)
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=NUM_TEST_CHATS)
    return client, crud_tester


def test_read_one(chat_crud_tester):
    client, crud_tester = chat_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(chat_crud_tester):
    client, crud_tester = chat_crud_tester
    crud_tester.test_read_many(client)


def test_create(chat_crud_tester):
    client, crud_tester = chat_crud_tester
    crud_tester.test_create(client)


def test_delete(chat_crud_tester):
    client, crud_tester = chat_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(chat_crud_tester):
    client, crud_tester = chat_crud_tester
    crud_tester.test_lifecycle(client)
