from unittest.mock import MagicMock
from unittest.mock import patch

from fastapi import status

from ichrisbirch.api.client.exceptions import APIConnectionError
from ichrisbirch.api.client.exceptions import APIHTTPError
from ichrisbirch.app.login import load_user
from tests.util import show_status_and_response


class TestLoadUserGracefulErrorHandling:
    """Test that load_user handles API errors gracefully.

    When the API returns an error (user not found, connection failure, etc.),
    load_user should return None instead of crashing. This allows Flask-Login
    to treat the session as invalid and redirect to the login page.

    This is a regression test for the bug where stale session cookies (e.g., after
    database reset or user deletion) would crash the app with APIHTTPError.
    """

    def test_load_user_returns_none_when_user_not_found(self, test_app_function):
        """load_user should return None when API returns 404 (user not found)."""
        mock_resource = MagicMock()
        mock_resource.get_generic.side_effect = APIHTTPError('User not found', status_code=404)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.resource.return_value = mock_resource

        with (
            test_app_function.application.test_request_context(),
            patch('ichrisbirch.app.login.get_users_api', return_value=mock_client),
        ):
            result = load_user('nonexistent_alternative_id')

        assert result is None

    def test_load_user_returns_none_when_api_unreachable(self, test_app_function):
        """load_user should return None when API connection fails."""
        mock_resource = MagicMock()
        mock_resource.get_generic.side_effect = APIConnectionError('Connection refused')

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.resource.return_value = mock_resource

        with (
            test_app_function.application.test_request_context(),
            patch('ichrisbirch.app.login.get_users_api', return_value=mock_client),
        ):
            result = load_user('some_alternative_id')

        assert result is None

    def test_load_user_returns_none_on_server_error(self, test_app_function):
        """load_user should return None when API returns 500 (server error)."""
        mock_resource = MagicMock()
        mock_resource.get_generic.side_effect = APIHTTPError('Internal server error', status_code=500)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.resource.return_value = mock_resource

        with (
            test_app_function.application.test_request_context(),
            patch('ichrisbirch.app.login.get_users_api', return_value=mock_client),
        ):
            result = load_user('some_alternative_id')

        assert result is None

    def test_stale_session_redirects_to_login(self, test_app_function):
        """App should redirect to login when session contains invalid user ID.

        This simulates the scenario where a user has a session cookie with an
        alternative_id that no longer exists in the database (e.g., after a
        database reset or user deletion).
        """
        mock_resource = MagicMock()
        mock_resource.get_generic.side_effect = APIHTTPError('User not found', status_code=404)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.resource.return_value = mock_resource

        with patch('ichrisbirch.app.login.get_users_api', return_value=mock_client):
            # Set a fake session cookie with an invalid user ID
            with test_app_function.session_transaction() as sess:
                sess['_user_id'] = 'invalid_alternative_id_12345'

            # Access a protected route - should redirect to login, not crash
            response = test_app_function.get('/tasks/', follow_redirects=False)

        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert '/login' in response.headers['Location']


class TestAdminLoginRequired:
    """Test the admin_login_required decorator.

    The decorator protects all routes in the admin blueprint via @blueprint.before_request.
    Tests verify:
    - Anonymous users are redirected to login
    - Regular logged-in users get unauthorized
    - Admin users can access admin routes
    """

    ADMIN_INDEX_URL = '/admin/'

    def test_anonymous_user_redirected_to_login(self, test_app_function):
        """Anonymous users should be redirected to the login page."""
        response = test_app_function.get(self.ADMIN_INDEX_URL, follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert '/login' in response.headers['Location']

    def test_regular_user_gets_unauthorized(self, test_app_logged_in_function):
        """Regular logged-in users (non-admin) should get unauthorized."""
        response = test_app_logged_in_function.get(self.ADMIN_INDEX_URL, follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert '/login' in response.headers['Location']

    def test_admin_user_can_access(self, test_app_logged_in_admin_function):
        """Admin users should be able to access admin routes."""
        response = test_app_logged_in_admin_function.get(self.ADMIN_INDEX_URL)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'Server Stats' in response.data or b'serverstats' in response.data.lower()

    def test_admin_route_returns_content_not_none(self, test_app_logged_in_admin_function):
        """Admin routes should return actual content, not None.

        This is a regression test for the bug where the decorator didn't call
        the wrapped function, causing all admin routes to return None/empty.
        """
        response = test_app_logged_in_admin_function.get(self.ADMIN_INDEX_URL)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.data) > 0, 'Admin route returned empty response'
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data, 'Admin route did not return HTML'
