from dataclasses import dataclass
from time import perf_counter

import httpx
import pendulum
import structlog

from ichrisbirch import schemas
from ichrisbirch.config import Settings

logger = structlog.get_logger()


@dataclass
class SmokeEndpoint:
    path: str
    name: str
    category: str
    auth_level: str


ENDPOINTS = [
    # Critical — must always work
    SmokeEndpoint('/health', 'Health Check', 'critical', 'public'),
    SmokeEndpoint('/tasks/', 'Tasks List', 'critical', 'user'),
    SmokeEndpoint('/articles/', 'Articles List', 'critical', 'user'),
    SmokeEndpoint('/books/', 'Books List', 'critical', 'user'),
    SmokeEndpoint('/habits/', 'Habits List', 'critical', 'user'),
    SmokeEndpoint('/admin/system/health/', 'System Health', 'critical', 'admin'),
    # Important — core features
    SmokeEndpoint('/tasks/todo/', 'Tasks Todo', 'important', 'user'),
    SmokeEndpoint('/tasks/completed/', 'Tasks Completed', 'important', 'user'),
    SmokeEndpoint('/articles/current/', 'Current Article', 'important', 'user'),
    SmokeEndpoint('/countdowns/', 'Countdowns', 'important', 'user'),
    SmokeEndpoint('/events/', 'Events', 'important', 'user'),
    SmokeEndpoint('/autotasks/', 'AutoTasks', 'important', 'user'),
    SmokeEndpoint('/users/me/', 'Current User', 'important', 'user'),
    SmokeEndpoint('/admin/scheduler/jobs/', 'Scheduler Jobs', 'important', 'admin'),
    SmokeEndpoint('/admin/config/', 'Environment Config', 'important', 'admin'),
    # Secondary — nice to have
    SmokeEndpoint('/server/', 'Server Stats', 'secondary', 'user'),
    SmokeEndpoint('/durations/', 'Durations', 'secondary', 'user'),
    SmokeEndpoint('/money-wasted/', 'Money Wasted', 'secondary', 'user'),
    SmokeEndpoint('/box-packing/boxes/', 'Boxes', 'secondary', 'user'),
    SmokeEndpoint('/box-packing/items/', 'Box Items', 'secondary', 'user'),
    SmokeEndpoint('/box-packing/items/orphans/', 'Orphaned Items', 'secondary', 'user'),
    SmokeEndpoint('/chat/chats/', 'Chats', 'secondary', 'user'),
    SmokeEndpoint('/chat/messages/', 'Chat Messages', 'secondary', 'user'),
    SmokeEndpoint('/api-keys/', 'API Keys', 'secondary', 'user'),
    SmokeEndpoint('/articles/failed-imports/', 'Failed Imports', 'secondary', 'user'),
    SmokeEndpoint('/habits/categories/', 'Habit Categories', 'secondary', 'user'),
    SmokeEndpoint('/habits/completed/', 'Completed Habits', 'secondary', 'user'),
    SmokeEndpoint('/admin/system/errors/', 'Recent Errors', 'secondary', 'admin'),
    SmokeEndpoint('/admin/scheduler/history/', 'Scheduler History', 'secondary', 'admin'),
    SmokeEndpoint('/admin/backups/', 'Backups', 'secondary', 'admin'),
]


async def run_smoke_tests(app, settings: Settings, admin_email: str) -> schemas.admin.SmokeTestReport:
    """Run smoke tests against all GET endpoints using ASGI transport (in-process)."""
    results: list[schemas.admin.SmokeTestResult] = []
    start = perf_counter()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://smoke-test') as client:
        for endpoint in ENDPOINTS:
            headers = {}
            if endpoint.auth_level in ('user', 'admin'):
                headers['Remote-User'] = admin_email
                headers['Remote-Email'] = admin_email

            result = await _test_endpoint(client, endpoint, headers)
            results.append(result)

    total_ms = (perf_counter() - start) * 1000
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    critical_results = [r for r in results if r.category == 'critical']
    all_critical_passed = all(r.passed for r in critical_results)

    report = schemas.admin.SmokeTestReport(
        run_at=pendulum.now().isoformat(timespec='seconds'),
        environment=settings.ENVIRONMENT,
        total=len(results),
        passed=passed,
        failed=failed,
        duration_ms=round(total_ms, 1),
        all_critical_passed=all_critical_passed,
        results=results,
    )

    logger.info(
        'smoke_tests_completed',
        total=report.total,
        passed=passed,
        failed=failed,
        duration_ms=report.duration_ms,
        all_critical_passed=all_critical_passed,
    )

    return report


async def _test_endpoint(
    client: httpx.AsyncClient,
    endpoint: SmokeEndpoint,
    headers: dict[str, str],
) -> schemas.admin.SmokeTestResult:
    """Test a single endpoint and return the result."""
    start = perf_counter()
    try:
        response = await client.get(endpoint.path, headers=headers, timeout=5.0)
        elapsed_ms = (perf_counter() - start) * 1000
        passed = 200 <= response.status_code < 300

        if not passed:
            logger.warning(
                'smoke_test_failed',
                path=endpoint.path,
                status_code=response.status_code,
                response_time_ms=round(elapsed_ms, 1),
            )

        return schemas.admin.SmokeTestResult(
            path=endpoint.path,
            name=endpoint.name,
            category=endpoint.category,
            auth_level=endpoint.auth_level,
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 1),
            passed=passed,
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.error('smoke_test_error', path=endpoint.path, error=str(e))
        return schemas.admin.SmokeTestResult(
            path=endpoint.path,
            name=endpoint.name,
            category=endpoint.category,
            auth_level=endpoint.auth_level,
            response_time_ms=round(elapsed_ms, 1),
            passed=False,
            error=str(e),
        )
