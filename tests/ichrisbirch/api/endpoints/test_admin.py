import pytest
from ichrisbirch.api.endpoints import admin

from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data
from tests.utils.database import get_test_login_users


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('users')
    yield
    delete_test_data('users')


def test_websocket_log_stream(test_api_logged_in_admin):
    test_logs = ['Test log 1', 'Test log 2', 'Test log 3']
    
    class MockLogReader:
        def get_logs(self):
            return test_logs
    
    app = test_api_logged_in_admin.app
    app.dependency_overrides[admin.get_log_reader] = lambda: MockLogReader()
    
    with test_api_logged_in_admin.websocket_connect('/admin/log-stream/') as websocket:
        # Get the logs from the websocket
        logs = [websocket.receive_text() for _ in range(len(test_logs))]
        assert logs == test_logs
