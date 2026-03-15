"""Tests for admin system health, error buffer, and config API endpoints."""

from unittest.mock import patch

from fastapi import status

from tests.util import show_status_and_response

HEALTH_ENDPOINT = '/admin/system/health/'
ERRORS_ENDPOINT = '/admin/system/errors/'
CONFIG_ENDPOINT = '/admin/config/'


class TestSystemHealthAuth:
    """Test system health endpoint authentication."""

    def test_health_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.get(HEALTH_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_health_unauthenticated(self, test_api):
        response = test_api.get(HEALTH_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


class TestSystemHealth:
    """Test system health endpoint responses."""

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_health_returns_all_sections(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []

        response = test_api_logged_in_admin.get(HEALTH_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert 'server' in data
        assert 'docker' in data
        assert 'database' in data
        assert 'redis' in data
        assert 'disk' in data

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_health_server_info(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []

        response = test_api_logged_in_admin.get(HEALTH_ENDPOINT)
        data = response.json()
        assert data['server']['environment'] == 'testing'
        assert 'server_time' in data['server']

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_health_database_stats(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []

        response = test_api_logged_in_admin.get(HEALTH_ENDPOINT)
        data = response.json()
        assert 'tables' in data['database']
        assert 'total_size_mb' in data['database']
        assert 'active_connections' in data['database']
        assert data['database']['total_size_mb'] > 0

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_health_disk_usage(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []

        response = test_api_logged_in_admin.get(HEALTH_ENDPOINT)
        data = response.json()
        assert data['disk']['total_gb'] > 0
        assert data['disk']['percent_used'] > 0


class TestRecentErrors:
    """Test recent errors endpoint."""

    def test_errors_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.get(ERRORS_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_errors_returns_list(self, test_api_logged_in_admin):
        response = test_api_logged_in_admin.get(ERRORS_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert isinstance(response.json(), list)


class TestEnvironmentConfig:
    """Test environment config endpoint."""

    def test_config_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.get(CONFIG_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_config_returns_sections(self, test_api_logged_in_admin):
        response = test_api_logged_in_admin.get(CONFIG_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        section_names = [s['name'] for s in data]
        assert 'auth' in section_names
        assert 'postgres' in section_names

    def test_config_masks_secrets(self, test_api_logged_in_admin):
        response = test_api_logged_in_admin.get(CONFIG_ENDPOINT)
        data = response.json()
        auth_section = next(s for s in data if s['name'] == 'auth')
        assert auth_section['settings']['jwt_secret_key'] == '***MASKED***'
        assert auth_section['settings']['internal_service_key'] == '***MASKED***'

    def test_config_shows_non_sensitive_values(self, test_api_logged_in_admin):
        response = test_api_logged_in_admin.get(CONFIG_ENDPOINT)
        data = response.json()
        general_section = next(s for s in data if s['name'] == '_general')
        assert general_section['settings']['ENVIRONMENT'] == 'testing'
