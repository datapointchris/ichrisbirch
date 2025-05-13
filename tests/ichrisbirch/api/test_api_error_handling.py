"""Tests for API error handling across different endpoints.

This module tests how the API handles various error conditions including:
- Authentication errors
- Invalid input validation
- Resource not found errors
- Permission errors
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from ichrisbirch import schemas


class TestAPIErrorHandling:
    """Test API error handling across different endpoints."""

    def test_unauthorized_access(self, test_api):
        """Test that unauthenticated requests to protected endpoints are rejected."""
        # Try accessing a protected endpoint without authentication
        response = test_api.get('/tasks/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Check for proper error message structure
        error_data = response.json()
        assert 'detail' in error_data
        assert 'Invalid credentials' in error_data['detail']
    
    def test_invalid_auth_token(self, test_api):
        """Test handling of invalid authentication token."""
        # Send an invalid token in Authorization header
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = test_api.get('/tasks/', headers=headers)
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
            "category": "Home",
            "priority": 1
        }
        response = test_api_logged_in.post('/tasks/', json=invalid_task)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Check error details
        error_data = response.json()
        assert 'detail' in error_data
        
        # Find the specific validation error for the missing name field
        errors = error_data['detail']
        assert any(error['loc'][1] == 'name' for error in errors)
    
    def test_invalid_enum_value(self, test_api_logged_in):
        """Test validation errors with invalid enum values."""
        # Try to create a task with invalid category
        invalid_task = {
            "name": "Test Task",
            "category": "InvalidCategory",  # Invalid enum value
            "priority": 1
        }
        response = test_api_logged_in.post('/tasks/', json=invalid_task)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Check error details for enum validation error
        error_data = response.json()
        assert 'detail' in error_data
    
    def test_method_not_allowed(self, test_api_logged_in):
        """Test handling of unsupported HTTP methods."""
        # Try to use PATCH on an endpoint that doesn't support it
        response = test_api_logged_in.patch('/tasks/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.skip(reason='no valid admin endpoint for testing')
    def test_unauthorized_admin_endpoint(self, test_api_logged_in):
        """Test that regular users cannot access admin endpoints."""
        # Try to access admin endpoint with regular user
        response = test_api_logged_in.get('/admin/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.skip(reason='no valid admin endpoint for testing')
    def test_admin_endpoint_with_admin_user(self, test_api_logged_in_admin):
        """Test that admin users can access admin endpoints."""
        # Access admin endpoint with admin user
        response = test_api_logged_in_admin.get('/admin/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_invalid_json_format(self, test_api_logged_in):
        """Test handling of malformed JSON."""
        # Send malformed JSON in request body
        headers = {"Content-Type": "application/json"}
        response = test_api_logged_in.post(
            '/tasks/', 
            headers=headers,
            data="{invalid-json:"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_query_parameters(self, test_api_logged_in):
        """Test handling of invalid query parameters."""
        # Send invalid query parameter type
        response = test_api_logged_in.get('/tasks/?priority=not_a_number')
        
        # Should either return 422 for validation error or empty results
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK]
        
        if response.status_code == status.HTTP_200_OK:
            # If API validates params but returns empty results, that's valid too
            assert response.json() == []