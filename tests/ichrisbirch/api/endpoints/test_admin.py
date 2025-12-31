from ichrisbirch.api.endpoints import admin
from tests.utils.database import insert_test_data_transactional


def test_websocket_log_stream(txn_api_logged_in_admin):
    client, session = txn_api_logged_in_admin
    insert_test_data_transactional(session, 'users')

    test_logs = ['Test log 1', 'Test log 2', 'Test log 3']

    class MockLogReader:
        def get_logs(self):
            return test_logs

    app = client.app
    app.dependency_overrides[admin.get_log_reader] = MockLogReader

    with client.websocket_connect('/admin/log-stream/') as websocket:
        # Get the logs from the websocket
        logs = [websocket.receive_text() for _ in range(len(test_logs))]
        assert logs == test_logs
