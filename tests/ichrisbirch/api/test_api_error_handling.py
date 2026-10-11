"""Tests for API error handling across different endpoints.

This module tests how the API handles various error conditions including:
- Authentication errors
- Invalid input validation
- Resource not found errors
- Permission errors
"""

from fastapi import status


class TestAPIErrorHandling:
    """Test API error handling across different endpoints."""

    def test_unauthorized_access(self, test_api):
        """Test that unauthenticated requests to protected endpoints are rejected."""
        # Try accessing a protected endpoint without authentication
        response = test_api.get('/tasks')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check for proper error message structure
        error_data = response.json()
        assert 'message' in error_data
        assert 'Invalid credentials' in error_data['message']

    def test_invalid_auth_token(self, test_api):
        """Test handling of invalid authentication token."""
        # Send an invalid token in Authorization header
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = test_api.get('/tasks', headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_resource_not_found(self, test_api_logged_in):
        """Test that 404 Not Found is returned when accessing nonexistent resources."""
        # Try to access a nonexistent task
        nonexistent_id = 999999  # Assuming this ID doesn't exist
        response = test_api_logged_in.get(f'/tasks/{nonexistent_id}')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_validation_error_invalid_data(self, test_api_logged_in):
        """Test validation errors when sending invalid data."""
        # Try to create a task with missing required fields
        invalid_task = {
            # Missing 'name' field
            'category': 'Home',
            'window_days': 1,
        }
        response = test_api_logged_in.post('/tasks', json=invalid_task)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # Check error details
        error_data = response.json()
        assert 'errors' in error_data

        # Find the specific validation error for the missing name field
        errors = error_data['errors']
        assert any(error['loc'][1] == 'name' for error in errors)

    def test_unauthorized_admin_endpoint(self, test_api_logged_in):
        """A signed-in user who is not an admin is known, so the refusal is a 403 rather than a 401."""
        response = test_api_logged_in.get('/admin/config')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_endpoint_with_admin_user(self, test_api_logged_in_admin):
        response = test_api_logged_in_admin.get('/admin/config')
        assert response.status_code == status.HTTP_200_OK
