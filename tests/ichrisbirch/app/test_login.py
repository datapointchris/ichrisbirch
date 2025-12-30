from fastapi import status

from tests.util import show_status_and_response


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
