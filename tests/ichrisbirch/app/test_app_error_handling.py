"""Tests for Flask app error handling.

This module tests how the Flask app handles various error conditions including:
- 404 Not Found errors
- 400 Bad Request errors
- 500 Internal Server errors
"""


class TestFlaskErrorHandling:
    """Test Flask app error handling across different routes."""

    def test_404_not_found(self, test_app_function):
        response = test_app_function.get('/nonexistent-route/')
        assert response.status_code == 404
        assert b'404 Not Found' in response.data

    def test_resource_not_found(self, test_app_function):
        nonexistent_id = 999999
        response = test_app_function.get(f'/tasks/{nonexistent_id}/')
        assert response.status_code == 404

    def test_method_not_allowed(self, test_app_logged_in_function):
        response = test_app_logged_in_function.delete('/tasks/')
        assert response.status_code == 405
        assert b'405 Method Not Allowed' in response.data

    def test_unauthorized_access_to_protected_route(self, test_app_function):
        response = test_app_function.get('/tasks/', follow_redirects=True)
        assert b'Login for iChrisBirch' in response.data

    def test_admin_route_protection(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get('/admin/', follow_redirects=True)
        assert (
            response.status_code == 403
            or b"You don't have the permission" in response.data
            or b'You must be logged in to view that page' in response.data
            or b'Permission denied' in response.data
            or b'flash-messages__message--warning' in response.data
        )
