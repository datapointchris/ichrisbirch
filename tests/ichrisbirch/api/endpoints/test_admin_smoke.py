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
    def test_smoke_all_endpoints_pass(self, mock_docker, test_api_logged_in_admin):
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        failed = [r for r in data['results'] if not r['passed']]
        assert data['failed'] == 0, f'Failed endpoints: {[(r["path"], r["status_code"], r.get("error")) for r in failed]}'

    @patch('ichrisbirch.api.endpoints.admin._get_docker_containers')
    def test_smoke_discovers_core_endpoints(self, mock_docker, test_api_logged_in_admin):
        """Verify autodiscovery isn't filtering too aggressively."""
        mock_docker.return_value = []
        response = test_api_logged_in_admin.post(SMOKE_ENDPOINT)
        data = response.json()
        paths = {r['path'] for r in data['results']}
        assert '/health' in paths
        assert '/tasks/' in paths
        assert '/articles/' in paths
        assert '/books/' in paths
