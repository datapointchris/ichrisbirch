"""Tests for admin smoke test endpoint."""

from unittest.mock import patch

from fastapi import status

from tests.util import show_status_and_response

SMOKE_ENDPOINT = '/admin/smoke-tests/'


class TestSmokeTestAuth:
    """Test smoke test endpoint authentication."""

    def test_smoke_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.post(SMOKE_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_smoke_unauthenticated(self, test_api):
        response = test_api.post(SMOKE_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


class TestSmokeTests:
    """Test smoke test endpoint responses."""

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_returns_report(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert 'results' in data
        assert 'total' in data
        assert 'passed' in data
        assert 'failed' in data
        assert 'all_critical_passed' in data
        assert 'run_at' in data
        assert 'environment' in data
        assert data['total'] > 0

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_all_endpoints_pass(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        data = response.json()
        failed = [r for r in data['results'] if not r['passed']]
        assert data['failed'] == 0, f'Failed endpoints: {[(r["path"], r["status_code"], r.get("error")) for r in failed]}'
        assert data['passed'] == data['total']

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_has_all_categories(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        data = response.json()
        categories = {r['category'] for r in data['results']}
        assert 'critical' in categories
        assert 'important' in categories
        assert 'secondary' in categories

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_critical_endpoints_present(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        data = response.json()
        critical_paths = {r['path'] for r in data['results'] if r['category'] == 'critical'}
        assert '/health' in critical_paths
        assert '/tasks/' in critical_paths
        assert '/articles/' in critical_paths
        assert '/books/' in critical_paths

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_result_structure(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        data = response.json()
        result = data['results'][0]
        assert 'path' in result
        assert 'name' in result
        assert 'category' in result
        assert 'auth_level' in result
        assert 'status_code' in result
        assert 'response_time_ms' in result
        assert 'passed' in result
