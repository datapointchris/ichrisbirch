"""Tests for admin system health, error buffer, and config API endpoints."""

import asyncio
import socket
import threading
import time
from collections.abc import Callable
from unittest.mock import patch

import httpx2
import pytest
from fastapi import status
from sqlalchemy import text

from ichrisbirch import schemas
from ichrisbirch.api.endpoints import admin
from ichrisbirch.database.session import create_session
from tests.util import show_status_and_response
from tests.utils.database import get_test_runner_settings

HEALTH_ENDPOINT = '/admin/system/health/'
ERRORS_ENDPOINT = '/admin/system/errors/'
CONFIG_ENDPOINT = '/admin/config/'

SLOW_PROBE_SECONDS = 2
SHORT_PROBE_TIMEOUT_SECONDS = 0.2
PROBE_DEADLINE_SECONDS = 2


def finish_within[T](seconds: float, probe: Callable[[], T]) -> T:
    """Run the probe on a daemon thread, so a probe that never returns fails the test instead of hanging it."""
    result: list[T] = []
    thread = threading.Thread(target=lambda: result.append(probe()), daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        pytest.fail(f'probe still running after {seconds}s')
    return result[0]


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


class TestSystemHealthProbes:
    """A dependency that is slow, silent or refusing reads as unavailable and holds no other request."""

    @pytest.mark.asyncio
    async def test_a_slow_probe_does_not_delay_a_concurrent_request(self, test_api_logged_in_admin):
        probe_started = threading.Event()
        started_at: list[float] = []

        def slow_redis_probe(settings):
            started_at.append(time.monotonic())
            probe_started.set()
            time.sleep(SLOW_PROBE_SECONDS)
            return schemas.admin.RedisStats(key_count=0, memory_used_human='N/A', connected_clients=0, uptime_seconds=0)

        # TestClient gives each request its own event loop, so one loop is driven here the way uvicorn drives it.
        transport = httpx2.ASGITransport(app=test_api_logged_in_admin.app)
        with (
            patch('ichrisbirch.api.endpoints.admin._get_docker_containers', return_value=[]),
            patch('ichrisbirch.api.endpoints.admin._get_redis_stats', slow_redis_probe),
        ):
            async with httpx2.AsyncClient(transport=transport, base_url='http://test') as client:
                health = asyncio.create_task(client.get(HEALTH_ENDPOINT))
                assert await asyncio.to_thread(probe_started.wait, SLOW_PROBE_SECONDS * 2)
                errors = await client.get(ERRORS_ENDPOINT)
                answered_after = time.monotonic() - started_at[0]
                health_response = await health

        assert errors.status_code == status.HTTP_200_OK, show_status_and_response(errors)
        assert health_response.status_code == status.HTTP_200_OK, show_status_and_response(health_response)
        assert answered_after < SLOW_PROBE_SECONDS / 2

    def test_a_redis_that_refuses_auth_reads_as_unavailable_before_the_probe_timeout(self):
        settings = get_test_runner_settings()
        settings.redis.password = 'not-the-test-redis-password'

        started = time.monotonic()
        stats = admin._get_redis_stats(settings)

        assert stats.memory_used_human == 'N/A'
        assert time.monotonic() - started < admin.PROBE_TIMEOUT_SECONDS

    def test_a_redis_that_never_answers_reads_as_unavailable(self):
        with socket.create_server(('127.0.0.1', 0)) as silent:
            settings = get_test_runner_settings()
            settings.redis.host, settings.redis.port = silent.getsockname()
            settings.redis.password = ''
            with patch.object(admin, 'PROBE_TIMEOUT_SECONDS', SHORT_PROBE_TIMEOUT_SECONDS):
                stats = finish_within(PROBE_DEADLINE_SECONDS, lambda: admin._get_redis_stats(settings))

        assert stats.memory_used_human == 'N/A'

    def test_a_docker_daemon_that_never_answers_reads_as_unavailable(self, monkeypatch):
        with socket.create_server(('127.0.0.1', 0)) as silent:
            host, port = silent.getsockname()
            monkeypatch.setenv('DOCKER_HOST', f'tcp://{host}:{port}')
            monkeypatch.delenv('DOCKER_TLS_VERIFY', raising=False)
            with patch.object(admin, 'PROBE_TIMEOUT_SECONDS', SHORT_PROBE_TIMEOUT_SECONDS):
                containers = finish_within(PROBE_DEADLINE_SECONDS, admin._get_docker_containers)

        assert containers == []

    def test_a_database_query_past_the_probe_timeout_reads_as_unavailable(self):
        with (
            create_session(get_test_runner_settings()) as session,
            patch.object(admin, 'PROBE_TIMEOUT_SECONDS', SHORT_PROBE_TIMEOUT_SECONDS),
            patch.object(admin, 'TABLE_ROW_COUNTS_SQL', text('SELECT pg_sleep(5)')),
        ):
            stats = finish_within(PROBE_DEADLINE_SECONDS, lambda: admin._get_database_stats(session))

        assert stats == schemas.admin.DatabaseStats(tables=[], total_size_mb=0, active_connections=0)


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
