"""Tests for admin API endpoints including WebSocket log streaming."""

import tempfile
from pathlib import Path

import pytest
from starlette.websockets import WebSocketDisconnect

from ichrisbirch.api.endpoints import admin
from ichrisbirch.api.endpoints.admin import ANSI_ESCAPE_PATTERN
from ichrisbirch.api.endpoints.admin import LogReader

# =============================================================================
# LogReader Unit Tests
# =============================================================================


class TestANSIEscapePattern:
    """Test ANSI escape code stripping."""

    def test_strips_color_codes(self):
        """Test that common ANSI color codes are stripped."""
        # Green text
        assert ANSI_ESCAPE_PATTERN.sub('', '\x1b[32mgreen\x1b[0m') == 'green'
        # Bold
        assert ANSI_ESCAPE_PATTERN.sub('', '\x1b[1mbold\x1b[0m') == 'bold'
        # Multiple codes
        assert ANSI_ESCAPE_PATTERN.sub('', '\x1b[1m\x1b[32mbold green\x1b[0m') == 'bold green'

    def test_strips_structlog_console_format(self):
        """Test stripping ANSI codes from actual structlog ConsoleRenderer output."""
        # Actual structlog output with colors
        colored_log = '\x1b[2m2026-01-14T07:00:18Z\x1b[0m [\x1b[32m\x1b[1minfo     \x1b[0m] \x1b[1mlogging_initialized\x1b[0m'
        expected = '2026-01-14T07:00:18Z [info     ] logging_initialized'
        assert ANSI_ESCAPE_PATTERN.sub('', colored_log) == expected

    def test_preserves_plain_text(self):
        """Test that plain text without ANSI codes is unchanged."""
        plain = '2026-01-14T07:00:18Z [info     ] logging_initialized'
        assert ANSI_ESCAPE_PATTERN.sub('', plain) == plain

    def test_handles_empty_string(self):
        """Test handling of empty strings."""
        assert ANSI_ESCAPE_PATTERN.sub('', '') == ''


class TestLogReader:
    """Test LogReader class."""

    def test_get_logs_nonexistent_directory(self):
        """Test that nonexistent directory returns empty list."""
        reader = LogReader(log_dir='/nonexistent/path/that/does/not/exist')
        logs = list(reader.get_logs())
        assert logs == []

    def test_get_logs_empty_directory(self):
        """Test that empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = LogReader(log_dir=tmpdir)
            logs = list(reader.get_logs())
            assert logs == []

    def test_get_logs_reads_log_files(self):
        """Test that log files are read correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test log file
            log_file = Path(tmpdir) / 'test.log'
            log_file.write_text('line1\nline2\nline3\n')

            reader = LogReader(log_dir=tmpdir)
            logs = list(reader.get_logs())

            assert len(logs) == 3
            assert 'line1' in logs[0]
            assert 'line2' in logs[1]
            assert 'line3' in logs[2]

    def test_get_logs_strips_ansi_codes(self):
        """Test that ANSI codes are stripped from log lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            # Write log with ANSI codes
            log_file.write_text('\x1b[32mgreen text\x1b[0m\n')

            reader = LogReader(log_dir=tmpdir)
            logs = list(reader.get_logs())

            assert len(logs) == 1
            assert logs[0].strip() == 'green text'
            assert '\x1b' not in logs[0]

    def test_get_logs_multiple_files_sorted(self):
        """Test that multiple log files are read in sorted order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in non-alphabetical order
            (Path(tmpdir) / 'z_last.log').write_text('last\n')
            (Path(tmpdir) / 'a_first.log').write_text('first\n')
            (Path(tmpdir) / 'm_middle.log').write_text('middle\n')

            reader = LogReader(log_dir=tmpdir)
            logs = list(reader.get_logs())

            # Should be sorted alphabetically
            assert 'first' in logs[0]
            assert 'middle' in logs[1]
            assert 'last' in logs[2]

    def test_get_logs_ignores_non_log_files(self):
        """Test that non-.log files are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / 'test.log').write_text('log content\n')
            (Path(tmpdir) / 'test.txt').write_text('txt content\n')
            (Path(tmpdir) / 'readme.md').write_text('readme\n')

            reader = LogReader(log_dir=tmpdir)
            logs = list(reader.get_logs())

            assert len(logs) == 1
            assert 'log content' in logs[0]


# =============================================================================
# WebSocket Endpoint Tests
# =============================================================================


class TestWebSocketLogStreamAuth:
    """Test WebSocket log stream authentication."""

    def test_websocket_no_token_rejected(self, txn_api):
        """Test that WebSocket without access_token cookie is rejected."""
        client, session = txn_api

        # Mock the log reader to avoid file system dependencies
        class MockLogReader:
            def get_logs(self):
                return ['test log']

        client.app.dependency_overrides[admin.get_log_reader] = MockLogReader

        # Connect without any cookies - should be rejected
        with pytest.raises(WebSocketDisconnect):  # noqa: SIM117
            with client.websocket_connect('/admin/log-stream/') as websocket:
                websocket.receive_text()

    def test_websocket_invalid_token_rejected(self, txn_api):
        """Test that WebSocket with invalid token is rejected."""
        client, session = txn_api

        class MockLogReader:
            def get_logs(self):
                return ['test log']

        client.app.dependency_overrides[admin.get_log_reader] = MockLogReader

        # Set invalid token cookie
        client.cookies.set('access_token', 'Bearer invalid_token_here')

        with pytest.raises(WebSocketDisconnect):  # noqa: SIM117
            with client.websocket_connect('/admin/log-stream/') as websocket:
                websocket.receive_text()

    def test_websocket_non_admin_rejected(self, txn_api_logged_in, insert_users_for_login):
        """Test that WebSocket with non-admin user token is rejected."""
        client, session = txn_api_logged_in

        class MockLogReader:
            def get_logs(self):
                return ['test log']

        client.app.dependency_overrides[admin.get_log_reader] = MockLogReader

        # Get a valid token for regular (non-admin) user
        # The txn_api_logged_in fixture authenticates as regular user
        # We need to get a JWT token for this user
        from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
        from ichrisbirch.config import get_settings

        settings = get_settings()
        # Create a mock token handler without database session (just for token creation)
        # We'll mock the session in the token handler

        # Get the regular user from the database
        from sqlalchemy import select

        from ichrisbirch.models import User

        regular_user = session.execute(select(User).where(User.email == 'testloginregular@testuser.com')).scalar_one()

        # Create token handler with session
        token_handler = JWTTokenHandler(settings=settings, session=session)
        access_token = token_handler.create_access_token(str(regular_user.alternative_id))

        # Set the token as cookie
        client.cookies.set('access_token', f'Bearer {access_token}')

        with pytest.raises(WebSocketDisconnect):  # noqa: SIM117
            with client.websocket_connect('/admin/log-stream/') as websocket:
                websocket.receive_text()


class TestWebSocketLogStreamFunctionality:
    """Test WebSocket log streaming functionality with admin auth."""

    def test_websocket_admin_can_connect_and_receive_logs(self, txn_api_logged_in_admin, insert_users_for_login):
        """Test that admin user can connect via WebSocket and receive logs."""
        client, session = txn_api_logged_in_admin

        test_logs = ['Log line 1', 'Log line 2', 'Log line 3']

        class MockLogReader:
            def get_logs(self):
                return test_logs

        client.app.dependency_overrides[admin.get_log_reader] = MockLogReader

        # Get the admin user and create a valid JWT token
        from sqlalchemy import select

        from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
        from ichrisbirch.config import get_settings
        from ichrisbirch.models import User

        settings = get_settings()
        admin_user = session.execute(select(User).where(User.email == 'testloginadmin@testadmin.com')).scalar_one()

        token_handler = JWTTokenHandler(settings=settings, session=session)
        access_token = token_handler.create_access_token(str(admin_user.alternative_id))

        # Set the token as cookie
        client.cookies.set('access_token', f'Bearer {access_token}')

        with client.websocket_connect('/admin/log-stream/') as websocket:
            received_logs = [websocket.receive_text() for _ in range(len(test_logs))]
            assert received_logs == test_logs

    def test_websocket_streams_logs_with_ansi_stripped(self, txn_api_logged_in_admin, insert_users_for_login):
        """Test that ANSI codes are stripped from streamed logs."""
        client, session = txn_api_logged_in_admin

        # Logs with ANSI codes
        test_logs_with_ansi = ['\x1b[32mgreen\x1b[0m', '\x1b[1mbold\x1b[0m']
        expected_logs = ['green', 'bold']

        class MockLogReader:
            def get_logs(self):
                # Simulate what LogReader does - strip ANSI codes
                for log in test_logs_with_ansi:
                    yield ANSI_ESCAPE_PATTERN.sub('', log)

        client.app.dependency_overrides[admin.get_log_reader] = MockLogReader

        from sqlalchemy import select

        from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
        from ichrisbirch.config import get_settings
        from ichrisbirch.models import User

        settings = get_settings()
        admin_user = session.execute(select(User).where(User.email == 'testloginadmin@testadmin.com')).scalar_one()

        token_handler = JWTTokenHandler(settings=settings, session=session)
        access_token = token_handler.create_access_token(str(admin_user.alternative_id))

        client.cookies.set('access_token', f'Bearer {access_token}')

        with client.websocket_connect('/admin/log-stream/') as websocket:
            received_logs = [websocket.receive_text() for _ in range(len(expected_logs))]
            assert received_logs == expected_logs
