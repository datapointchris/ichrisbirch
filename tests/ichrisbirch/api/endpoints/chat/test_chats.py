import pytest

from ichrisbirch import schemas
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from ..crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('chats')
    yield
    delete_test_data('chatmessages', 'chats')  # Order matters: messages first due to FK


ENDPOINT = '/chat/chats/'
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

crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


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
